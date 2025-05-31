namespace HelloWorld
{
    public class RoutingMiddleware
    {
        public RoutingMiddleware(RequestDelegate _)
        {
        }
        public async Task InvokeAsync(HttpContext context)
        {
            string path = context.Request.Path;
            if (path == "/index")
            {
                await context.Response.WriteAsync("Home Page");
            }
            else if (path == "/about")
            {
                await context.Response.WriteAsync("About Page");
            }
            else
            {
                context.Response.StatusCode = 404;
            }
        }
    }
}
