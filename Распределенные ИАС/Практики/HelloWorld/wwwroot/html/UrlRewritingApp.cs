using System.Text.RegularExpressions;
using Microsoft.AspNetCore.Rewrite;
using Microsoft.Net.Http.Headers;

namespace UrlRewritingApp
{
    public class RedirectPHPRequests : IRule
    {
        private readonly string _extension;
        private readonly PathString _newPath;

        public RedirectPHPRequests(string extension, string newPath)
        {
            if (string.IsNullOrEmpty(extension))
            {
                throw new ArgumentException(nameof(extension));
            }
            if (!Regex.IsMatch(newPath, @"(/[A-Za-z0-9]+)+?"))
            {
                throw new ArgumentException("Запрошенный путь недействителен", nameof(newPath));
            }

            _extension = extension;
            _newPath = new PathString(newPath);
        }

        public void ApplyRule(RewriteContext context)
        {
            var request = context.HttpContext.Request;
            var pathValue = request.Path.Value; // запрошенный путь

            if (request.Path.StartsWithSegments(new PathString(_newPath))) return;

            if (pathValue != null && pathValue.EndsWith(".php", StringComparison.OrdinalIgnoreCase))
            {
                var response = context.HttpContext.Response;

                response.StatusCode = StatusCodes.Status301MovedPermanently;
                context.Result = RuleResult.EndResponse;
                response.Headers[HeaderNames.Location] = _newPath + pathValue.Substring(0, pathValue.Length - 3) + _extension;
            }
        }
    }
}