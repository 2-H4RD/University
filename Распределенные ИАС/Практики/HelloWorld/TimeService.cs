namespace HelloWorld
{
    public class TimeService
    {
        private ITimer timer;
        public TimeService(ITimer timer)
        {
            this.timer = timer;
        }
        public string GetTime() => timer.Time;
    }
}
