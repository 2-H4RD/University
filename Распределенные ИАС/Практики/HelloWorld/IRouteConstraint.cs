namespace HelloWorld
{
    public interface IRouteConstraint
    {
        bool Match(HttpContext? httpContext,
                IRouter? route,
                string routeKey,
                RouteValueDictionary values,
                RouteDirection routeDirection);
    }
}
