var fadeInOut = function(fadeIn, d3Selection, durationTime) {
    if (fadeIn === "in") {
        var start = 0;
        var end = 1;
    }
    else if (fadeIn === "out") {
        var start = 1;
        var end = 0;
    }
    else {
        return;
    }

    d3.select(d3Selection)
        .style("opacity", start)
        .transition()
        .duration(durationTime)
        .style("opacity", end);
}

var array2Table = function(genre_name, data, columns_obj) {

    var solidBlack = function(d3Obj) {
        d3Obj.style("border", "1.4px solid black")
    };
    d3.select("#topGamesContent").select("#topGames").html("");
	
    var table = d3.select("#topGamesContent").select("#topGames");

    var tCaption = table.append("caption")
        .classed("text-center", true)
        .style("font-family", "PT Sans");

    var thead = table.append("thead");
    var tbody = table.append("tbody");
    
    tCaption.html(genre_name);

    solidBlack(table);

    thead.append("tr")
        .selectAll("th")
        .data(columns_obj)
        .enter()
        .append("th")
        .text(function(d) { return d["column"]; })
        .each(function(d) {
                var th = d3.select(this);
                solidBlack(th);
                var styles = d["styles"];
                if (styles) {
                    styles.forEach(function(s) {
                        th.style(s[0], s[1]);
                    })
                }
            });

    //row for each object in arr
    var rows = tbody.selectAll("tr")
            .data(data)
            .enter()
            .append("tr")
            .attr("rowid", function(d) { return d.id; })
            .attr("chosen", false)
            .attr("onclick", function(d) {
                    return "steamDetails(" + d.id + ")";
            });

    var cells = rows.selectAll("td")
        .data(function(row) {
              return columns_obj.map(function(col_obj) {
                  return {
                            column: col_obj["column"],
                            value: row[col_obj["column"]],
                            styles: col_obj["styles"],
                            format: col_obj["format"]
                  }
              });
        })
        .enter()
        .append("td")
        .text(function(d) {
              if (d["format"]) {
                return d["format"](d["value"]);
              }
              else { return d["value"]; }
        })
        .each(function(d) {
                var td = d3.select(this);
                solidBlack(td);
                var styles = d["styles"];
                if (styles) {
                    //console.log(styles);
                    styles.forEach(function(s) {
                        td.style(s[0], s[1]);
                    })
                }
            });

    //console.log(table);
    fadeInOut("in", "#topGamesContent", 400);
    //  return table
}

var steamDetails = function(id) {
    console.log(STEAM_ID);
    if (parseInt(id) === STEAM_ID) {
        console.log("id: " + id + " just checked.");
        return 0;
    }
    else { STEAM_ID = parseInt(id); }

    STEAM_COUNTER += 1;
    if (STEAM_COUNTER > 100 && STEAM_COUNTER <= 150) {
	console.log("approaching the steam api threshold: " + STEAM_COUNTER);
        return 0;
    }
    if (STEAM_COUNTER > 150) {
        STEAM_COUNTER = 0;
    }

    //console.log("hitting /details");
    var url = "/details/" + id;

    d3.json(url, function(error, json) {
        if (error) {
            console.log(error);
        }
        else {

            var u = json["header_image"];
            var ending = u.match("\.jpg.*")[0];
            var header_url = u.replace(ending, ".jpg");
            var detailsBox = d3.select("#steamDetailsBox");
		
            detailsBox.select("#headerImage").selectAll("img").remove();
            detailsBox.select("#platforms").selectAll("i").remove();
            detailsBox.select("#metacritic").selectAll("a").remove();

            var headerImageContent = detailsBox.select("#headerImage")
                    .append("img")
                    .attr("src", header_url)
                    .classed("image-responsive", true)
                    .style("width", "90%")
                    .style("border", "2px");
                
            var platforms = json["platforms"];
            if (platforms) {

                var platformMappings = {
                    "windows": "fa fa-windows",
                    "linux": "fa fa-linux",
                    "mac": "fa fa-apple",
                }

                for (var i in platforms) {
                    if (platforms[i]) {
                        var platformClass = platformMappings[i];

                        detailsBox.select("#platforms")
                            .append("i")
                            .classed(platformClass, true)
                            .attr("aria-hidden", "true")
                            .style("padding", "2px");
                    }
                }
            }
            var metacritic = json["metacritic"];
            if (metacritic) {
                var score = metacritic["score"];
                var metacriticUrl = metacritic["url"];

                detailsBox.select("#metacritic").select("#metacriticScore")
                    .append("a")
                    .attr("href", metacriticUrl)
                    .attr("target", "_blank")
                    .html("Metascore: " + score);
            }
            detailsBox.classed("hidden", false);
            fadeInOut("in", "#steamDetailsBox", 400);
        }
    })
};

var loadGraph = function() {

    var barPadding = 1;
    var xScale = d3.scale.ordinal()
        .domain(initialData.map(function(d) { return d[1]; }))
        .rangeRoundBands([0, w - margin["left"] - margin["right"]], .1, .3);

    var xAxis = d3.svg.axis()
        .scale(xScale)
        .orient("bottom");

    var yScale = d3.scale.linear()
        .domain([0, d3.max(totals, function(d) { return d; })])
        .range([0, h - (margin["top"] + margin["bottom"])]);

    var bars = svg.selectAll("rect")
        .data(initialData)
        .enter()
        .append("rect")
        .attr("x", function(d, i) {
            return xScale(d[1]);
        })
        .attr("y", function(d) {
            return h - margin["bottom"] - margin["top"] -  yScale(d[2]); // each data element is an array of [genre_id, genre_name, count]
        })
        .attr("width", xScale.rangeBand() - barPadding)
        .attr("height", function(d) {
            return yScale(d[2]);
        })
        .attr("fill", function(d, i) {
                return colors(i);
        })
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
	
        //labels
        var valueLabels = svg.selectAll("text.value")
          .data(initialData)
          .enter()
          .append("text")
          .text(function(d) { return numericFormat(d[2]); })
          .attr("x", function(d, i) {
              var extraPadding = margin.left + margin.right;
              return xScale(d[1]) + extraPadding - 2;
          })
          .attr("y", function(d, i) {
              var barHeight = yScale(d[2]);
              var yMargin = h - margin["bottom"];
              var yPos = yMargin - barHeight - 7;

              return yPos;
          })
          .attr("text-anchor", "middle")
          .attr("font-family", "sans-serif")
          .attr("font-size", "9px")
          .attr("font-weight", "bold");

        var genreLabels = svg.append("g")
            .attr("class", "x axis")
            .attr("transform",function (d) {
                    var xVal = String(margin.left);
                    var yVal = String(h - margin.bottom);
                    return "translate(" + xVal + "," + yVal + ")";
                  })
            .call(xAxis)
          .selectAll(".tick text")
            .call(wrap, xScale.rangeBand());

        var chartTitle = svg.append("text")
            .attr("x", (w/2))
            .attr("y", 0)
            .attr("text-anchor", "middle")
            .style("font-size", "18px")
            .style("font-family", "PT Sans")
            .attr("font-weight", "bold")
            .text("Steam genre popularity by active player count");

        var chartInfo = svg.append("text")
            .attr("x", (w/2))
            .attr("y", margin.top/2)
            .attr("text-anchor", "middle")
            .style("font-size", "14px")
            .style("font-family", "PT Sans")
            .attr("font-weight", "bold")
            .text("click on a given genre for more info");

	
        return [xScale, bars, valueLabels, genreLabels, chartTitle, chartInfo];
    };

//https://bl.ocks.org/mbostock/7555321
var wrap = function (text, width) {
  text.each(function() {
    var text = d3.select(this),
        words = text.text().split(/\s+/).reverse(),
        word,
        line = [],
        lineNumber = 0,
        lineHeight = 1.1, // ems
        y = text.attr("y"),
        dy = parseFloat(text.attr("dy")),
        tspan = text.text(null).append("tspan").attr("x", 0).attr("y", y).attr("dy", dy + "em");
    while (word = words.pop()) {
      line.push(word);
      tspan.text(line.join(" "));
      if (tspan.node().getComputedTextLength() > width) {
        line.pop();
        tspan.text(line.join(" "));
        line = [word];
        tspan = text.append("tspan").attr("x", 0).attr("y", y).attr("dy", ++lineNumber * lineHeight + dy + "em").text(word);
      }
    }
  });
}
