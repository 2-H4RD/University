namespace HelloWorld
{
    // время в формате hh:mm:ss
    class LongTimeService : ITimeService
    {
        public string GetTime() => DateTime.Now.ToLongTimeString();
    }
}
