using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace user_to_network_API.Migrations
{
    public partial class netstatSimpleString : Migration
    {
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "ConnectionState",
                table: "NetstatResultDto");

            migrationBuilder.DropColumn(
                name: "DestinationIp",
                table: "NetstatResultDto");

            migrationBuilder.DropColumn(
                name: "PID",
                table: "NetstatResultDto");

            migrationBuilder.DropColumn(
                name: "Protocol",
                table: "NetstatResultDto");

            migrationBuilder.RenameColumn(
                name: "SourceIp",
                table: "NetstatResultDto",
                newName: "Connection");
        }

        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.RenameColumn(
                name: "Connection",
                table: "NetstatResultDto",
                newName: "SourceIp");

            migrationBuilder.AddColumn<string>(
                name: "ConnectionState",
                table: "NetstatResultDto",
                type: "nvarchar(max)",
                nullable: false,
                defaultValue: "");

            migrationBuilder.AddColumn<string>(
                name: "DestinationIp",
                table: "NetstatResultDto",
                type: "nvarchar(max)",
                nullable: false,
                defaultValue: "");

            migrationBuilder.AddColumn<string>(
                name: "PID",
                table: "NetstatResultDto",
                type: "nvarchar(max)",
                nullable: false,
                defaultValue: "");

            migrationBuilder.AddColumn<string>(
                name: "Protocol",
                table: "NetstatResultDto",
                type: "nvarchar(max)",
                nullable: false,
                defaultValue: "");
        }
    }
}
