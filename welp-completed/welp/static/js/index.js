// Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0  

var current_cuisine = "";
var loading = false;

var chartColors = {
    red: 'rgb(255, 99, 132)',
    orange: 'rgb(255, 159, 64)',
    yellow: 'rgb(255, 205, 86)',
    green: 'rgb(75, 192, 192)',
    blue: 'rgb(54, 162, 235)',
    purple: 'rgb(153, 102, 255)',
    grey: 'rgb(201, 203, 207)'
};

function onCuisineChange(cuisine) {
    current_cuisine = cuisine;
    
    $('#current_cuisine').text(current_cuisine);

    $('#rfreq_wrapper').hide();
    $('#body_wrapper').show();

    $('#cuisine_selection').val([current_cuisine]);

    $('div#clear').click(function() {
        $('#cuisine_selection').val([]);

        $('#rfreq_wrapper').show();
        $('#body_wrapper').hide();
    });
    
    var list = $('ul#' + cuisine);
    if (!list.length) {
        refreshDataSet();
    } else {
        list.show();
    }
}

function onFrequencyGraphClick(e, element) {
    onCuisineChange(element[0]._view.label);
}

function buildFrequencyGraph() {
    var barConfig = {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Restaurants',
                backgroundColor: chartColors.purple,
                data: []
            }]
        },
        options: {
            responsive: true,
            title: {
                display: true,
                text: 'Restaurants by Frequency'
            },
            legend: {
                display: false
            },
            onClick: onFrequencyGraphClick,
        },
    };
    return new Chart(document.getElementById("rfreq").getContext("2d"), barConfig);
}

function buildRatingsGraph() {
    var config = {
        type: 'pie',
        data: {
            datasets: [{
                data: [],
                backgroundColor: [
                    chartColors.red,
                    chartColors.orange,
                    chartColors.yellow,
                    chartColors.green,
                    chartColors.blue,
                ],
                label: 'Restaurant Ratings'
            }],
            labels: []
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            title: {
                display: true,
                text: 'Restaurant Ratings'
            },
            legend: {
                position: 'bottom',
                labels: {
                    fontColor: "black",
                    boxWidth: 20,
                    padding: 20
                }
            },
        }
    };
    return new Chart(document.getElementById("ratings").getContext("2d"), config);
}

function buildMap() {
    mymap = L.map('map').setView(currentLocation, 13);
    L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
        attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
        maxZoom: 18,
        id: 'mapbox.streets',
        accessToken: mapAccessToken,
    }).addTo(mymap);

    mymap.on('moveend', refreshDataSet);

    return mymap;
}

function onRestaurantDetail(item) {
    var params = {'id': item.attr('id')};
    $.getJSON('/restaurant_detail', $.param(params), function(result) {
        var name = item.attr("id");
        var name_nocolons = name.replace(/:/, '');
        var table = $('<table id="' + item.attr("id") + '"/>');
        var tr = $('<tr/>');
        var th = $('<th/>');
        var td = $('<td/>');
        var stars = $('<div/>', { class: 'rate' });
        for (var i = 5; i > 0; i--) {
            stars.append($('<input/>', { type: 'radio', id: 'star' + i + name_nocolons, name: 'rate' + name, value: i }));
            stars.append($('<label/>', { for: 'star' + i + name_nocolons, title: i }).text(i + ' Stars'));
        }
        var headers = tr.clone().append(th.clone().text("Key")).append(th.clone().text("Value"));
        table.append(headers);
        tr.clone().append(td.clone().text("Rating")).append(td.clone().append(stars)).appendTo(table);
        $.getJSON('/rating', "id=" + item.attr("id"), function(rating) {
            if (rating != null) {
                table.find('input#star' + rating + name_nocolons).prop("checked", true);
            }
        });
        $.each(result, function(key, val) {
            if (key.startsWith("tag:") && key != "tag:cuisine" && key != "tag:name") {
                key = key.replace(/tag:/, '').replace(/_/, ' ').replace(/addr:/, '');
                key = key.charAt(0).toUpperCase() + key.slice(1);
                var row = tr.clone().append(td.clone().text(key)).append(td.clone().text(val));
                table.append(row);
            }
        });

        item.append(table);
    });   
}

function updateTable(cuisine, result) {
    return function(result) {
        var li = $('<li/>');
        var div = $('<div/>');

        // Create a list of all restaurants
        var ul = $('<ul/>', {'id': cuisine, 'class': 'restaurants'});
        $.each(result, function(key, val) {
            if (val == null) {
                val = key;
            }

            ul.append(li.clone().attr('id', key).append(div.clone().attr('class', 'link').append(div.clone().attr('class', 'label').text(val))));
        });

        // Replace existing list with new one
        $('ul.restaurants').replaceWith(ul);

        // Clicking on a restaurant will expand its detail page
        $('li .label').bind('click', function() {
            var item = $(this).parent().parent();

            var tables = item.children('table');

            if (!tables.length) {
                onRestaurantDetail(item);
            } else {
                tables.toggle();
            }
        });
    }
};

function updateMap(result) {
    // Remove the prior restaurants within the added layer group
    mymap.eachLayer(function(layer) {
        if (layer instanceof L.LayerGroup) {
            mymap.removeLayer(layer);
        }
    });

    var layerGroup = L.layerGroup();
    $.each(result, function(restaurant, latlon) {
        L.marker([latlon[1], latlon[0]]).addTo(layerGroup).bindPopup("Loading...").on('click', function(e) {
            
            // Move list entry up to the top and expand it
            var listEntry = $(document).find('li#' + restaurant.replace(/:/, '\\:'));

            listEntry.detach().prependTo($(document).find('ul.restaurants'));
            listEntry.find('div').trigger("click");

            // Set the popup for the marker to be the name of the restaurant
            var popup = e.target.getPopup();
            var params = {'id': restaurant, 'field': 'tag:name'};
            $.getJSON('/restaurant_detail', $.param(params), function(result) {
                var display = 'Unknown'
                if ('tag:name' in result) {
                    display = result['tag:name']
                }
                popup.setContent(display);
            });
        });
    });
    layerGroup.addTo(mymap);
};

function refreshDataSet() {
    var bounds = mymap.getBounds().getNorthWest().distanceTo(mymap.getBounds().getSouthEast());
    var params = {'cuisine': current_cuisine, 'lng': mymap.getCenter().lng, 'lat': mymap.getCenter().lat, 'diag': bounds};
    $.getJSON('/restaurant_list', $.param(params), updateTable(current_cuisine));
    $.getJSON('/map_data', $.param(params), updateMap);
    refreshRatingsGraph();
}

function updateProgressBar(progress) {
    $("#progressbar").progressbar({
        value: progress
    });
    $("#progressbar > span").html(progress + "%");
}

function refreshProgress() {
    $.getJSON('/import_progress', function(result) {
        var loading = result['running'];
        var progress = result['progress'];

        if (progress > 0 && loading) {
            updateProgressBar(progress);
        }

        if (loading) {
            var timer = setTimeout(refreshProgress, 100);
            $('input#reload').attr('value', 'Stop Import');
        } else {
            $('input#reload').attr('value', 'Import Data');
            refreshFrequencyGraph();
            if ($("#progressbar").progressbar("instance")) {
                $("#progressbar").progressbar("destroy");
            }
            $("#progressbar > span").html("");
        }
    });
}

function refreshRatingsGraph() {
    var params = { cuisine: current_cuisine };
    $.getJSON('/cuisine_ratings', $.param(params),
        function(result) {
            var new_labels = [];
            var new_values = [];
            $.each(result, function(key, val) {
                new_labels.push(key + ' Star');
                new_values.push(val);
            });

            ratingsGraph.data.datasets[0].data = new_values;
            ratingsGraph.data.labels = new_labels;
            ratingsGraph.update();
        }
    );
}

function refreshFrequencyGraph() {
    $.getJSON('/restaurant_frequencies',
        function(result) {
            var new_labels = [];
            var new_values = [];
            var i = 0;
            $.each(result, function(key, val) {
                if (++i < 10) {
                    new_labels.push(key);
                    new_values.push(val);
                }
                $("#cuisine_selection").append($('<option>', {
                    value: key,
                    text: key,
                }));
                $('#cuisine_selection').val([]);
            });
            
            freqGraph.data.datasets[0].data = new_values;
            freqGraph.data.labels = new_labels;
            freqGraph.update();
        }
    );
}

var freqGraph = buildFrequencyGraph();
var ratingsGraph = buildRatingsGraph();
var mymap = buildMap();

$(document).ready(function() {
    $('#body_wrapper').hide();

    // Update page on load
    refreshFrequencyGraph();
    refreshProgress();

    $('input#reload').click(function() {
        if (loading) {
            $.getJSON('/stop_import');
        }
        else {
            $.getJSON('/start_import');
            updateProgressBar(0);
        }
        setTimeout(refreshProgress, 100);
    });

    $('input#clear_ratings').click(function() {
        $.getJSON('/clear_ratings');

        ratingsGraph.data.datasets[0].data = [0, 0, 0, 0, 0];
        ratingsGraph.update();
        $('.rate input').prop("checked", false);
    });

    $('input#button').click(refreshFrequencyGraph);
    
    $("#cuisine_selection").change(function() {
        var option = $(this).find('option:selected').text();
        onCuisineChange(option);
    });

    $(document).on('click', '.rate input', function(e) {
        var item = $(e.target);
        var params = { 'id':  item.parents('table').attr('id'), 'rating': item.val() };
        $.getJSON('/rating', $.param(params),
            function(rating) {
                if (rating != item.val()) {
                    item.prop("checked", false);
                }
                refreshRatingsGraph();
            }
        );
        return true;
    });
});