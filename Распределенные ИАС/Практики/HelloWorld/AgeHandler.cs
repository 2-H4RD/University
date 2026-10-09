namespace HelloWorld
{
    using System.Security.Claims;
    using Microsoft.AspNetCore.Authorization;

    class AgeHandler : AuthorizationHandler<AgeRequirement>
    {
        protected override Task HandleRequirementAsync(AuthorizationHandlerContext context,
            AgeRequirement requirement)
        {
            // получаем claim с типом ClaimTypes.DateOfBirth - год рождения
            var yearClaim = context.User.FindFirst(c => c.Type == ClaimTypes.DateOfBirth);
            if (yearClaim is not null)
            {
                // если claim года рождения хранит число
                if (int.TryParse(yearClaim.Value, out var year))
                {
                    // и разница между текущим годом и годом рождения больше требуемого возраста
                    if ((DateTime.Now.Year - year) >= requirement.Age)
                    {
                        context.Succeed(requirement); // сигнализируем, что claim соответствует ограничению
                    }
                }
            }
            return Task.CompletedTask;
        }
    }
}
