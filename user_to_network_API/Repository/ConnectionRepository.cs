using AutoMapper;
using Microsoft.EntityFrameworkCore;
using Microsoft.VisualBasic;
using user_to_network_API.Data;
using user_to_network_API.Models;
using user_to_network_API.Models.Dtos;
using user_to_network_API.Repository.IRepository;

namespace user_to_network_API.Repository
{
    public class ConnectionRepository : IConnectionRepository
    {
        private readonly ApplicationDbContext _db;
        private readonly IMapper _mapper;

        public ConnectionRepository(ApplicationDbContext db, IMapper mapper)
        {
            _db = db;
            _mapper = mapper;
        }
        public async Task<ResponseDto<ConnectionDto>> CreateConnection(ConnectionDto newConnectionDto)
        {
            // Check if there is a valid info record
            var newConnection = _mapper.Map<ConnectionDto, Connection>(newConnectionDto);
            var response = new ResponseDto<ConnectionDto>();

            // Create
            _db.Connection.Add(newConnection);
            response.Data = _mapper.Map<Connection, ConnectionDto>(newConnection);
            response.status = true;
            response.message = "connection received: id " + newConnection.Id;


            await _db.SaveChangesAsync();

            return response;
        }

        public async Task<ResponseDto<List<Connection>>> ObtainConnection()
        {
            var response = new ResponseDto<List<Connection>>();
            try
            {
                response.Data = _db.Connection.ToList();
            }
            catch (Exception ex)
            {
                throw ex;
            }
            return response;
        }
    }
}
