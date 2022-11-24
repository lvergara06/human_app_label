using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace user_to_network_API.Migrations
{
    public partial class addmigrationconnections : Migration
    {
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "NetstatResultDto");

            migrationBuilder.DropTable(
                name: "Prototype");

            migrationBuilder.CreateTable(
                name: "Connection",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    Protocol = table.Column<string>(type: "nvarchar(max)", nullable: false),
                    SourceIp = table.Column<string>(type: "nvarchar(max)", nullable: false),
                    SourcePort = table.Column<string>(type: "nvarchar(max)", nullable: false),
                    DestinationIp = table.Column<string>(type: "nvarchar(max)", nullable: false),
                    DestinationPort = table.Column<string>(type: "nvarchar(max)", nullable: false),
                    status = table.Column<string>(type: "nvarchar(max)", nullable: false),
                    pid = table.Column<string>(type: "nvarchar(max)", nullable: false),
                    userSelection = table.Column<string>(type: "nvarchar(max)", nullable: false),
                    epochTime = table.Column<string>(type: "nvarchar(max)", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Connection", x => x.Id);
                });
        }

        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "Connection");

            migrationBuilder.CreateTable(
                name: "Prototype",
                columns: table => new
                {
                    id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    website = table.Column<string>(type: "nvarchar(max)", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Prototype", x => x.id);
                });

            migrationBuilder.CreateTable(
                name: "NetstatResultDto",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    Connection = table.Column<string>(type: "nvarchar(max)", nullable: false),
                    Prototypeid = table.Column<int>(type: "int", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_NetstatResultDto", x => x.Id);
                    table.ForeignKey(
                        name: "FK_NetstatResultDto_Prototype_Prototypeid",
                        column: x => x.Prototypeid,
                        principalTable: "Prototype",
                        principalColumn: "id");
                });

            migrationBuilder.CreateIndex(
                name: "IX_NetstatResultDto_Prototypeid",
                table: "NetstatResultDto",
                column: "Prototypeid");
        }
    }
}
