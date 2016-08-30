
var steamDetails = function(id) {
    var result = {};
    var url = "/details/" + id;
    d3.json(url, function(error, json) {
        if (error) {
            console.log(error);
            return;
        }
        else {
            console.log(json);
        }
    })
};
            /*var output = {
            "platforms": result["platforms"],
            "metaritic": result["metacritic"],
            "header_image": result["header_image"]
        };
        console.log(output);
        return output;
       
       }
    });

var derpDetails = function(id) {
    var url = "http://store.steampowered.com/api/appdetails?appids=" + id;
    d3.json(url).header("X-Requested-With", "XMLHTTPRequest").get(function(error, data) {
            var response = data;
            console.log(response);
            )}
    };
*/
