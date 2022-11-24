namespace user_to_network_API.Models
{
    public class Response<T>
    {
        public bool status { set; get; }
        public string message { set; get; }
        public T Data { get; set; }
    }
}
