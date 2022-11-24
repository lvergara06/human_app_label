namespace user_to_network_API.Models.Dtos
{
	public class ConnectionDto
	{
        public string Protocol { set; get; } = string.Empty;
        public string SourceIp { set; get; } = string.Empty;
        public string SourcePort { set; get; } = string.Empty;
        public string DestinationIp { set; get; } = string.Empty;
        public string DestinationPort { set; get; } = string.Empty;
        public string status { set; get; } = string.Empty;
        public string pid { set; get; } = string.Empty;
        public string userSelection { set; get; } = string.Empty;
        public long epochTime { set; get; }
    }
}
