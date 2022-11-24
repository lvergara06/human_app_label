using user_to_network_API.Models;
using user_to_network_API.Models.Dtos;

namespace user_to_network_API.Repository.IRepository
{
    public interface IConnectionRepository
    {
        public Task<ResponseDto<List<Connection>>> ObtainConnection();
        public Task<ResponseDto<ConnectionDto>> CreateConnection(ConnectionDto newConnectionDto);
    }
}
