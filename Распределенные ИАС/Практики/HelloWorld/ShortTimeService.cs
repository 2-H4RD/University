namespace HelloWorld
{
    // время в формате hh::mm
    class ShortTimeService : ITimeService
    {
        public string GetTime() => DateTime.Now.ToShortTimeString();
    }
}
