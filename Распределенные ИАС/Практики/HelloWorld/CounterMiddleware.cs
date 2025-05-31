namespace HelloWorld
{
    public class CounterMiddleware
    {
        RequestDelegate next;
        int i = 0; // счетчик запросов
        public CounterMiddleware(RequestDelegate next)
        {
            this.next = next;
        }
        public async Task InvokeAsync(HttpContext httpContext, ICounter counter, CounterService counterService)
        {
            i++;
            httpContext.Response.ContentType = "text/html;charset=utf-8";
            await httpContext.Response.WriteAsync($"Запрос {i}; Counter: {counter.Value}; Service: {counterService.Counter.Value}");
        }
    }
}
