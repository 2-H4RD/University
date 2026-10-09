namespace HelloWorld
{
    class TimeMessageMiddleware
    {
        private readonly RequestDelegate next;

        public TimeMessageMiddleware(RequestDelegate next)
        {
            this.next = next;
        }

        public async Task InvokeAsync(HttpContext context, ITimeService timeService)
        {
            context.Response.ContentType = "text/html;charset=utf-8";
            await context.Response.WriteAsync($"<h1>Time: {timeService.GetTime()}</h1>");
        }
    }
}
