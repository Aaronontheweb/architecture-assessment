namespace Example;

public static class Usage
{
    public static bool Run()
    {
        var policy = new Billing.RetryPolicy(3);
        var attempt = new Billing.Params(1);
        var report = new Reporting.Params("Summary");
        return policy.ShouldRetry(attempt.Attempts, report.Title.Length > 0);
    }
}
