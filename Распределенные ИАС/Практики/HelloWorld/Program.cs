var builder = WebApplication.CreateBuilder();
var app=builder.Build();
app.Run(async (context) =>
{
    context.Response.ContentType= "text/html; charset=utf-8";
    var stringBuilder = new System.Text.StringBuilder("<table>");
    foreach(var header in context.Request.Headrs)
});
app.Run();
