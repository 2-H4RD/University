namespace HelloWorld
{
    public class RandomCounter : ICounter
    {
        static Random rnd = new Random();
        private int _value;
        public RandomCounter()
        {
            _value = rnd.Next(0, 1000000);
        }
        public int Value
        {
            get => _value;
        }
    }
}
