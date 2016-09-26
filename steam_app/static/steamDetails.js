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

var array2Table = function(data, columns_obj) {

    var solidBlack = function(d3Obj) {
        d3Obj.style("border", "1.4px solid black")
    };
    d3.select("#topGamesContent").select("#topGames").html("");

    //var tableSvg = d3.select("#topBoxContent")
    //    .append("svg")
    //        .attr("width", w/2
    //        .attr("height", h/2 + margin.top + margin.bottom)
    //    .append("g")
    //        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
    //var table = .select("#topBoxContent").append("table")

    //var tableDiv = d3.select("#topGamesContent")
    //                  .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var table = d3.select("#topGamesContent").select("#topGames");

    //var table = tableSvg.append("table")
    //              //.style("border-collapse", "collapse")
    //              .classed("table", true)
    //              .classed("table-hover", true)
    //              .classed("table-condensed", true)
    //              .attr("align", "center");
    var thead = table.append("thead");
    var tbody = table.append("tbody");

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

    console.log(table);
    //fadeInOut("out", "#topGamesContent", 0);
    fadeInOut("in", "#topGamesContent", 500);
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

    console.log("hitting /details");
    var url = "/details/" + id;

    d3.json(url, function(error, json) {
        if (error) {
            console.log(error);
        }
        else {

            var u = json["header_image"];
            var ending = u.match("\.jpg.*")[0];
            var header_url = u.replace(ending, ".jpg");

            //var currentTopBox = d3.select("#topBox").node();
            //var currentTopBoxStyle = currentTopBox["style"];
            ///var cssText = currentTopBoxStyle["cssText"];

            //var detailsBoxLeft = Math.floor(0.7 * w);
            //var detailsBoxHeight = Math.floor(0.1 * h);
            //var px = "px";

            var detailsBox = d3.select("#steamDetailsBox");
            //    .style("left", detailsBoxLeft + px)
            //    .style("top", detailsBoxHeight + px);

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
                    .html("Metascore: " + score);
            }
            detailsBox.classed("hidden", false);
            fadeInOut("in", "#steamDetailsBox", 400);
            //var classed = d3.select("#steamDetailsBox").attr("class");
            //console.log(classed);

        }
    })
};

var loadGraph = function() {

    var barPadding = 1;
    var xScale = d3.scale.ordinal()
        .domain(initialData.map(function(d) { return d[1]; }))
        //.domain(d3.range(initialData.length))
        .rangeRoundBands([0, w - margin["left"] - margin["right"]], .1, .3);
        //.rangeRoundBands([0, w - (margin["left"] + margin["right"])], 0.05);

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
        //.on("mouseover", function(d) {
        //        var xPos = parseFloat(d3.select(this).attr("x")) + xScale.rangeBand();
        //        var yPos = parseFloat(d3.select(this).attr("y")) + 10;
        //        var px = "px";
        //        var lengthOfName = d[1].length;
        //        var lengthOfValue = String(d[1]).length;

        //        d3.select("#tooltip")
        //            .style("left", xPos + px)
        //            .style("top", yPos + px)
        //            .style("width", (lengthOfName + lengthOfValue) * 8 + px)
        //            .select("#genreName")
        //            .text(d[1]);

                //d3.select("#tooltip").select("#value")
                //    .text(numericFormat(d[2]));
                    //
        //        d3.select("#tooltip").classed("hidden", false);
        //});
        //labels
        var valueLabels = svg.selectAll("text.value")
          .data(initialData)
          .enter()
          .append("text")
          .text(function(d) { return numericFormat(d[2]); })
          .attr("x", function(d, i) {
              var extraPadding = margin.left + margin.right;
              return xScale(d[1]) + extraPadding;
          })
          .attr("y", function(d, i) {
              var barHeight = yScale(d[2]);
              var yMargin = h - margin["bottom"];
              var yPos = h - barHeight - margin["top"];

              //if (yPos >= yMargin - 5) {
              if (barHeight <= 36) {
                yPos = yMargin - barHeight - 7;
              }
              return yPos;
          })
          .attr("text-anchor", "middle")
          .attr("font-family", "sans-serif")
          .attr("font-size", "11px")
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

          /*var genreLabels = svg.selectAll("text.genre")
            .data(initialData)
            .enter()
            .append("text")
            .html(function(d) {
                genreName = "";
                if (d[1].search(" ") > 1) {
                    dSplit = d[1].split(" ");
                    words = [];
                    for (var i in dSplit) {
                      words.push(dSplit[i]);
                      words.push("<br />");
                    }
                  words.pop(-1);
                  genreName = words.join(" ");
                }
                else { genreName = d[1]; }

                return genreName;
            })
            .attr("x", function(d, i) {
              return xScale(i) + margin["left"] + margin["right"] + 5;
            })
            .attr("y", function(d, i) {
              var yMargin = h - margin["bottom"];
              return yMargin + 5;
            })
            .attr("writing-mode", "tb")
            .attr("font-family", "sans-serif")
            .attr("font-size", "11px")
            .attr("fill", "black");
          */

        return [xScale, bars, valueLabels, genreLabels];
    };

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
