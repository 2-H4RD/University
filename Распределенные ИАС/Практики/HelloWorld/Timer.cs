namespace HelloWorld
{
    public class Timer : ITimer
    {
        public Timer()
        {
            Time = DateTime.Now.ToLongTimeString();
        }
        public string Time { get; }
    }
}



