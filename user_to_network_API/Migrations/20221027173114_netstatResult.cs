using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace user_to_network_API.Migrations
{
    public partial class netstatResult : Migration
    {
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "description",
                table: "Prototype");

            migrationBuilder.AddColumn<int>(
                name: "descriptionId",
                table: "Prototype",
                type: "int",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.CreateTable(
                name: "NetstatResult",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    Protocol = table.Column<string>(type: "nvarchar(max)", nullable: false),
                    SourceIp = table.Column<string>(type: "nvarchar(max)", nullable: false),
                    DestinationIp = table.Column<string>(type: "nvarchar(max)", nullable: false),
                    ConnectionState = table.Column<string>(type: "nvarchar(max)", nullable: false),
                    PID = table.Column<string>(type: "nvarchar(max)", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_NetstatResult", x => x.Id);
                });

            migrationBuilder.CreateIndex(
                name: "IX_Prototype_descriptionId",
                table: "Prototype",
                column: "descriptionId");

            migrationBuilder.AddForeignKey(
                name: "FK_Prototype_NetstatResult_descriptionId",
                table: "Prototype",
                column: "descriptionId",
                principalTable: "NetstatResult",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);
        }

        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_Prototype_NetstatResult_descriptionId",
                table: "Prototype");

            migrationBuilder.DropTable(
                name: "NetstatResult");

            migrationBuilder.DropIndex(
                name: "IX_Prototype_descriptionId",
                table: "Prototype");

            migrationBuilder.DropColumn(
                name: "descriptionId",
                table: "Prototype");

            migrationBuilder.AddColumn<string>(
                name: "description",
                table: "Prototype",
                type: "nvarchar(max)",
                nullable: false,
                defaultValue: "");
        }
    }
}
