using HelloWorld;

public class TimerMiddleware
{
    RequestDelegate next;

    public TimerMiddleware(RequestDelegate next)
    {
        this.next = next;
    }

    public async Task InvokeAsync(HttpContext context, TimeService timeService)
    {
        if (context.Request.Path == "/time")
        {
            context.Response.ContentType = "text/html; charset=utf-8";
            await context.Response.WriteAsync($"Time: {timeService?.GetTime()}");
        }
        else
        {
            await next.Invoke(context);
        }
    }
}