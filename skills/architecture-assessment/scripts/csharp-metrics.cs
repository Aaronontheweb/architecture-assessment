#!/usr/bin/env -S dotnet --
#:property PublishAot=false
#:property TreatWarningsAsErrors=true
#:include $(MSBuildSDKsPath)/../Roslyn/bincore/Microsoft.CodeAnalysis.dll
#:include $(MSBuildSDKsPath)/../Roslyn/bincore/Microsoft.CodeAnalysis.CSharp.dll

using System.Diagnostics;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;

if (args.Length != 1)
{
    Console.Error.WriteLine("Usage: CsharpMetrics <clean-git-worktree>");
    return 2;
}

var root = Path.GetFullPath(args[0]);
ProcessStartInfo GitStart(params string[] arguments)
{
    var start = new ProcessStartInfo("git") { RedirectStandardOutput = true, UseShellExecute = false };
    start.ArgumentList.Add("-C");
    start.ArgumentList.Add(root);
    foreach (var argument in arguments) start.ArgumentList.Add(argument);
    return start;
}
string Git(params string[] arguments)
{
    using var process = Process.Start(GitStart(arguments)) ?? throw new InvalidOperationException("Cannot start Git");
    var output = process.StandardOutput.ReadToEnd();
    process.WaitForExit();
    if (process.ExitCode != 0) throw new InvalidOperationException("Git failed");
    return output;
}

if (!string.IsNullOrWhiteSpace(Git("status", "--porcelain", "--untracked-files=no")))
{
    Console.Error.WriteLine("Tracked worktree changes would invalidate the revision baseline.");
    return 1;
}

// Pin the input to committed Git blobs so checkout filters and line-ending conversion
// cannot change the measured source or its hash. Untracked files are outside this baseline.
var revision = Git("rev-parse", "HEAD").Trim();
var rows = new List<object>();
var declarations = new List<object>();
var occurrences = new List<object>();
var parsed = new List<(string Path, SyntaxTree Tree)>();
var entries = Git("ls-tree", "-rz", "--full-tree", revision).Split('\0', StringSplitOptions.RemoveEmptyEntries);
var batchStart = GitStart("cat-file", "--batch");
batchStart.RedirectStandardInput = true;
using var batch = Process.Start(batchStart) ?? throw new InvalidOperationException("Cannot start Git blob reader");
foreach (var entry in entries)
{
    var separator = entry.IndexOf('\t');
    var metadata = entry[..separator].Split(' ');
    var path = entry[(separator + 1)..];
    if (!path.EndsWith(".cs", StringComparison.Ordinal) || metadata[1] != "blob" || metadata[0] == "120000") continue;
    batch.StandardInput.WriteLine(metadata[2]);
    batch.StandardInput.Flush();
    // Each batch response is a header, exactly the advertised number of blob bytes,
    // and a trailing newline. Read the payload as bytes to preserve hashes and framing.
    var output = batch.StandardOutput.BaseStream;
    var header = new StringBuilder();
    for (var next = output.ReadByte(); next != '\n'; next = output.ReadByte())
    {
        if (next < 0) throw new InvalidOperationException("Incomplete Git blob header");
        header.Append((char)next);
    }
    var fields = header.ToString().Split(' ');
    if (fields.Length != 3 || fields[0] != metadata[2] || fields[1] != "blob")
        throw new InvalidOperationException("Git did not return the requested blob");
    var bytes = new byte[int.Parse(fields[2], System.Globalization.CultureInfo.InvariantCulture)];
    output.ReadExactly(bytes);
    if (output.ReadByte() != '\n') throw new InvalidOperationException("Invalid Git blob terminator");
    using var reader = new StreamReader(new MemoryStream(bytes), Encoding.UTF8, detectEncodingFromByteOrderMarks: true);
    var source = reader.ReadToEnd();
    // First pass: parse each file without a compilation or project-specific preprocessor
    // symbols, retain its tree for cross-file name matching, and record syntax metrics.
    var tree = CSharpSyntaxTree.ParseText(source, path: path);
    parsed.Add((path, tree));
    var syntax = tree.GetRoot();
    var nodes = syntax.DescendantNodes().ToArray();
    var constructors = new List<object>();
    foreach (var node in nodes)
    {
        var parameters = node switch
        {
            ConstructorDeclarationSyntax constructor => constructor.ParameterList,
            TypeDeclarationSyntax type => type.ParameterList,
            _ => null
        };
        if (parameters is null) continue;
        constructors.Add(new
        {
            line = tree.GetLineSpan(node.Span).StartLinePosition.Line + 1,
            kind = node.Kind().ToString(),
            parameters = parameters.Parameters.Count,
            defaulted_parameters = parameters.Parameters.Count(parameter => parameter.Default is not null)
        });
    }
    // Branch counts are a structural proxy, not cyclomatic complexity: only the listed
    // node kinds count, so keywords inside comments and strings contribute nothing.
    rows.Add(new
    {
        path,
        sha256 = Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant(),
        branch_nodes = nodes.Count(node => node is IfStatementSyntax or ForStatementSyntax
            or ForEachStatementSyntax or ForEachVariableStatementSyntax or WhileStatementSyntax
            or DoStatementSyntax or CatchClauseSyntax or ConditionalExpressionSyntax
            or SwitchSectionSyntax or SwitchExpressionArmSyntax),
        type_declarations = nodes.Count(node => node is BaseTypeDeclarationSyntax or DelegateDeclarationSyntax),
        method_declarations = nodes.Count(node => node is MethodDeclarationSyntax),
        defaulted_parameters = nodes.OfType<ParameterSyntax>().Count(parameter => parameter.Default is not null),
        directives = syntax.DescendantTrivia().Count(trivia => trivia.IsDirective),
        parse_errors = tree.GetDiagnostics().Where(d => d.Severity == DiagnosticSeverity.Error)
            .Select(d => new { id = d.Id, line = d.Location.GetLineSpan().StartLinePosition.Line + 1 }).ToArray(),
        constructors
    });
}
batch.StandardInput.Close();
batch.WaitForExit();
if (batch.ExitCode != 0) throw new InvalidOperationException("Git blob reader failed");

// Declaration IDs identify syntax locations, not compiler symbols. Partial declarations remain separate.
static bool IsDeclaration(SyntaxNode node) => node is BaseTypeDeclarationSyntax or DelegateDeclarationSyntax;
static string Name(SyntaxNode node) => node switch
{
    BaseTypeDeclarationSyntax type => type.Identifier.ValueText,
    DelegateDeclarationSyntax type => type.Identifier.ValueText,
    _ => throw new ArgumentException("Not a type declaration", nameof(node))
};
static int Arity(SyntaxNode node) => node switch
{
    TypeDeclarationSyntax type => type.TypeParameterList?.Parameters.Count ?? 0,
    DelegateDeclarationSyntax type => type.TypeParameterList?.Parameters.Count ?? 0,
    _ => 0
};
static string Id(string path, SyntaxNode node) => $"{path}:{node.SpanStart}";
static string QualifiedName(SyntaxNode node) => string.Join(".", node.AncestorsAndSelf().Reverse()
    .Where(n => n is BaseNamespaceDeclarationSyntax || IsDeclaration(n))
    .Select(n => n is BaseNamespaceDeclarationSyntax ns ? ns.Name.ToString()
        : Name(n) + (Arity(n) > 0 ? $"`{Arity(n)}" : "")));

// Gather names from every parsed file before the second pass so matching does not depend
// on file order. This is a simple-name filter, not namespace or compiler-symbol resolution.
var declaredNames = parsed.SelectMany(file => file.Tree.GetRoot().DescendantNodes().Where(IsDeclaration))
    .Select(Name).ToHashSet(StringComparer.Ordinal);
foreach (var (path, tree) in parsed)
{
    foreach (var node in tree.GetRoot().DescendantNodes().Where(IsDeclaration))
    {
        // Prune nested declaration bodies: their methods, branches, and constructors
        // belong to their own declaration rows, not to the enclosing type's metrics.
        var owned = node.DescendantNodes(descendIntoChildren: child => child == node || !IsDeclaration(child)).ToArray();
        var owner = node.Ancestors().FirstOrDefault(IsDeclaration);
        var span = tree.GetLineSpan(node.Span);
        declarations.Add(new
        {
            id = Id(path, node), path, name = Name(node), qualified_name = QualifiedName(node),
            arity = Arity(node), kind = node.Kind().ToString(),
            parent_id = owner is null ? null : Id(path, owner),
            line = span.StartLinePosition.Line + 1, end_line = span.EndLinePosition.Line + 1,
            modifiers = ((MemberDeclarationSyntax)node).Modifiers.Select(token => token.ValueText).ToArray(),
            bases = node is BaseTypeDeclarationSyntax type
                ? type.BaseList?.Types.Select(b => b.Type.ToString()).ToArray() ?? [] : [],
            method_declarations = owned.Count(n => n is MethodDeclarationSyntax),
            branch_nodes = owned.Count(n => n is IfStatementSyntax or ForStatementSyntax
                or ForEachStatementSyntax or ForEachVariableStatementSyntax or WhileStatementSyntax
                or DoStatementSyntax or CatchClauseSyntax or ConditionalExpressionSyntax
                or SwitchSectionSyntax or SwitchExpressionArmSyntax),
            max_constructor_parameters = owned.OfType<ConstructorDeclarationSyntax>()
                .Select(c => c.ParameterList.Parameters.Count)
                .Append(node is TypeDeclarationSyntax primary ? primary.ParameterList?.Parameters.Count ?? 0 : 0).Max()
        });
    }
    // Retain lexical candidates with their nearest declaration owner for later inspection.
    // Unrelated identifiers can match; aliases, implicit types, and reflection can be missed.
    foreach (var node in tree.GetRoot().DescendantNodes().OfType<SimpleNameSyntax>())
    {
        if (!declaredNames.Contains(node.Identifier.ValueText)) continue;
        var owner = node.Ancestors().FirstOrDefault(IsDeclaration);
        occurrences.Add(new
        {
            path, offset = node.SpanStart, line = tree.GetLineSpan(node.Span).StartLinePosition.Line + 1,
            name = node.Identifier.ValueText, arity = node is GenericNameSyntax generic ? generic.Arity : 0,
            owner_id = owner is null ? null : Id(path, owner),
            context = node.Parent?.Kind().ToString()
        });
    }
}

// Recheck before emitting any JSON so a detected revision or tracked-worktree change
// rejects the run instead of publishing it as a stable baseline.
if (Git("rev-parse", "HEAD").Trim() != revision
    || !string.IsNullOrWhiteSpace(Git("status", "--porcelain", "--untracked-files=no")))
{
    Console.Error.WriteLine("Revision or tracked worktree changed during collection; discard this run.");
    return 1;
}

Console.WriteLine(JsonSerializer.Serialize(new
{
    schema = 2,
    commit = revision,
    compiler = typeof(CSharpSyntaxTree).Assembly.GetName().Version?.ToString(),
    collector_sha256 = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(
        System.Reflection.Assembly.GetExecutingAssembly().Location))).ToLowerInvariant(),
    scope = "Committed regular files ending in lowercase .cs; symlinks skipped; generated/test files included; default preprocessor symbols; source and hashes read from Git blobs",
    branch_definition = "Counts if/loop/catch/conditional nodes and switch sections/arms; not cyclomatic complexity",
    reference_definition = "Lexical simple-name occurrences matching declared names; NOT bound references, runtime instances, or proof of use/non-use. Partial declarations remain separate. Aliases, implicit types, reflection, external consumers, and inactive preprocessor branches are incomplete.",
    files = rows,
    declarations,
    name_occurrences = occurrences
}, new JsonSerializerOptions { WriteIndented = true }));
return 0;
