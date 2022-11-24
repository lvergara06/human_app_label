using AutoMapper;
using Microsoft.VisualBasic;
using user_to_network_API.Models;
using user_to_network_API.Models.Dtos;
using System.Text.RegularExpressions;

namespace user_to_network_API.Mapper
{
    public class MappingProfile : Profile
    {
        public MappingProfile()
        {
            CreateMap<Connection, ConnectionDto>().ReverseMap();
        }
    }
}
