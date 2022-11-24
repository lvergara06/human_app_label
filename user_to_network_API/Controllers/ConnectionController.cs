using Microsoft.AspNetCore.Mvc;
using user_to_network_API.Models.Dtos;
using user_to_network_API.Repository.IRepository;

namespace user_to_network_API.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class ConnectionController : ControllerBase
    {
        private readonly IConnectionRepository _ConnectionRepository;
        public ConnectionController(IConnectionRepository PrototypeRepository)
        {
            _ConnectionRepository = PrototypeRepository;
        }
        [HttpPost("Create")]
        public async Task<IActionResult> Crear([FromBody] ConnectionDto ConnectionDto)
        {
            var result = await _ConnectionRepository.CreateConnection(ConnectionDto);
            return Ok(result);
        }
        [HttpGet("Obtain")]
        public async Task<IActionResult> Obtain()
        {
            var result = await _ConnectionRepository.ObtainConnection();
            return Ok(result);
        }
    }
}
