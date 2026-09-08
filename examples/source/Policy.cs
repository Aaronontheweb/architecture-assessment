namespace Example.Billing;

public sealed class RetryPolicy(int maxAttempts)
{
    public bool ShouldRetry(int attempts, bool transient)
    {
        if (!transient) return false;
        return attempts < maxAttempts;
    }
}

public sealed record Params(int Attempts);
