using Microsoft.AspNetCore.Authentication.Cookies;
using System.Security.Claims;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authorization;
using HelloWorld;

var people = new List <Person>
{
    new Person("tom@gmail.com", "12345", 1984),
    new Person("bob@gmail.com", "55555", 2006)
};

var builder = WebApplication.CreateBuilder();
// встраиваем сервис AgeHandler
builder.Services.AddTransient<IAuthorizationHandler, AgeHandler>();
builder.Services.AddAuthentication(CookieAuthenticationDefaults.AuthenticationScheme)
    .AddCookie(options =>
    {
        options.LoginPath = "/login";
        options.AccessDeniedPath = "/login";
    });
builder.Services.AddAuthorization(opts => {
    // устанавливаем ограничение по возрасту
    opts.AddPolicy("AgeLimit", policy => policy.Requirements.Add(new AgeRequirement(18)));
});

var app = builder.Build();

app.UseAuthentication();
app.UseAuthorization();

app.MapGet("/login", async (HttpContext context) =>
{
    context.Response.ContentType = "text/html; charset=utf-8";
    // html-форма для ввода логина/пароля
    string loginForm = @"<!DOCTYPE html>
    <html>
    <head>
        <meta charset='utf-8' />
    </head>
    <body>
        <h2>Login Form</h2>
        <form method='post'>
            <p>
                <label>Email</label><br />
                <input name='email' />
            </p>
            <p>
                <label>Password</label><br />
                <input type='password' name='password' />
            </p>
            <input type='submit' value='Login' />
        </form>
    </body>
    </html>";
    await context.Response.WriteAsync(loginForm);
});

app.MapPost("/login", async (string? returnUrl, HttpContext context) =>
{
    // получаем из формы email и пароль
    var form = context.Request.Form;
    // если email и/или пароль не установлены, посылаем статусный код ошибки 400
    if (!form.ContainsKey("email") || !form.ContainsKey("password"))
        return Results.BadRequest("Email и/или пароль не установлены");
    string email = form["email"];
    string password = form["password"];

    // находим пользователя 
    Person? person = people.FirstOrDefault(p => p.Email == email && p.Password == password);
    // если пользователь не найден, отправляем статусный код 401
    if (person is null) return Results.Unauthorized();
    var claims = new List<Claim>
    {
        new Claim(ClaimTypes.Name, person.Email),
        new Claim(ClaimTypes.DateOfBirth, person.Year.ToString())
    };
    var claimsIdentity = new ClaimsIdentity(claims, "Cookies");
    var claimsPrincipal = new ClaimsPrincipal(claimsIdentity);
    await context.SignInAsync(claimsPrincipal);
    return Results.Redirect(returnUrl ?? "/");
});
// доступ только для тех, кто соответствует ограничению AgeLimit
app.Map("/age", [Authorize(Policy = "AgeLimit")] () => "Age Limit is passed");

app.Map("/", [Authorize] (HttpContext context) =>
{
    var login = context.User.FindFirst(ClaimTypes.Name);
    var year = context.User.FindFirst(ClaimTypes.DateOfBirth);
    return $"Name: {login?.Value}\nYear: {year?.Value}";
});
app.MapGet("/logout", async (HttpContext context) =>
{
    await context.SignOutAsync(CookieAuthenticationDefaults.AuthenticationScheme);
    return "Данные удалены";
});

app.Run();

record class Person(string Email, string Password, int Year);