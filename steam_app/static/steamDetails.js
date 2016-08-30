var steamDetails = function(id) {
    var result = {};
    var url = "/details/" + id;
    var header_url;
    d3.json(url, function(error, json) {
        if (error) {
            console.log(error);
        }
        else {
            var u = json["header_image"];
            var ending = u.match("\.jpg.*")[0];
            header_url = u.replace(ending, ".jpg");

        }
        console.log(header_url);
    })

    d3.select("#steamDetailsBox")
        .append("<img href='" + header_url + "' />");

};
