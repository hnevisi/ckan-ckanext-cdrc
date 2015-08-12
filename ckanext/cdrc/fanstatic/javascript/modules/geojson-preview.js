this.ckan.module('geojson-preview', function ($, _) {
  $(document).ready(function(){
    $.ajax($('#map-container').attr('data-src')).done(function(data){

      var geojson = JSON.parse(data);
      if(geojson.title)
        $('#map-title').html(geojson.title + ' - Preview (Sample)');
      else
        $('#map-title').html('Map Preview (Sample)');
      var valMin, valMax;
      for(var i in geojson.features) {
        var val = geojson.features[i].properties.value
        if(!valMin || valMin >= val)
          valMin = val;
        if(!valMax || valMax <= val)
          valMax = val;
      }
      var colorMap = chroma.scale(['#FFEDA0', '#800026']).domain([valMin, valMax], 7, 'log');


      function style(feature) {
        return {
          fillColor: colorMap(feature.properties.value).hex(),
          weight: 0,
          opacity: 1,
          color: 'white',
          fillOpacity: 0.7
        };
      }

      var map = L.map('map-container');
      var features = L.geoJson(geojson, {style: style})
      features.addTo(map);
      map.fitBounds(features.getBounds());
      var info = L.control();

      var legend = L.control({position: 'bottomright'});

      legend.onAdd = function (map) {

          var div = L.DomUtil.create('div', 'info legend'),
              grades = colorMap.domain(),
              labels = [];

          // loop through our density intervals and generate a label with a colored square for each interval
          for (var i = 0; i < grades.length - 1; i++) {
              div.innerHTML +=
                  '<i style="background:' + colorMap(grades[i] + 1) + '"></i> ' +
                  grades[i].toFixed(2) + (grades[i + 1] ? '&ndash;' + grades[i + 1].toFixed(2) + '<br>' : '+');
          }

          return div;
      };

      legend.addTo(map);
    });

  });
});
