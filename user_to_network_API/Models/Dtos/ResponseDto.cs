namespace user_to_network_API.Models.Dtos
{
    public class ResponseDto<T>
    {
        public bool status { set; get; } = true;
        public string message { set; get; } = String.Empty;
        public T Data { get; set; }
    }
}
