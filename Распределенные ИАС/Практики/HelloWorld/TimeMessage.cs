namespace HelloWorld
{
    class TimeMessage
    {
        ITimeService timeService;
        public TimeMessage(ITimeService timeService)
        {
            this.timeService = timeService;
        }
        public string GetTime() => $"Time: {timeService.GetTime()}";
    }
}
