# C# implementation flavor

Apply these choices within the project's supported language/runtime and existing contracts. They are
ways to express the shared principles, not prerequisites for using the skill in another language.

- Prefer `internal` for new implementation types and `sealed` for classes, including record classes,
  unless a real consumer needs visibility or inheritance. Choose member visibility just as deliberately.
  Never narrow or seal a released extension point without a compatibility decision.
- Prefer records or other immutable value-oriented types for data. `record` and `init` do not make a
  referenced `List<T>` immutable; a read-only view can still reflect mutations through another alias.
  Choose immutable collections or defensive ownership as needed. Do not convert identity-bearing or
  lifecycle-owning objects to records simply to meet a keyword preference.
- Use value objects with controlled construction to enforce meaningful invariants. Check that default
  struct values, deserialization, and `with` expressions cannot bypass the promised validity rules.
  Choose a representation that actually provides the guarantee rather than adding wrappers by habit.
- Use distinct result/state variants and pattern matching when they clarify legal outcomes. Do not
  claim compile-time exhaustiveness for an open class hierarchy; use the guarantees the selected
  representation and compiler actually provide, backed by appropriate checks.
- Required dependencies belong in explicit construction contracts. An optional parameter or nullable
  value should represent a real optional state, not make a broken composition root appear to work.
  Preserve existing optional-parameter contracts when compatibility requires them.
- Compose focused collaborators rather than introducing a base-class hierarchy to reuse a few methods.
  An interface with one implementation can be justified by an actual boundary; it is neither mandatory
  nor automatically wasteful. Prefer a named responsibility over a generic service locator.
- Keep an actor, its private messages, or similar small supporting types with their cohesive unit when
  readable. Do not create `.Enums`, `.Abstractions`, or `.Helpers` namespaces solely by declaration kind.
  Independently shared contracts and real dependency boundaries can warrant separate files or assemblies.
- Use straightforward branches or named operations where nested ternaries or dense LINQ obscure behavior.
  Retain established failure visibility; do not add catch-all defaults or alternate implementations
  without an explicit recovery contract. Validate the affected positive and negative boundaries.
