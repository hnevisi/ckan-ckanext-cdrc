this.ckan.module('typesetting', function () {
  if($(window).width() >= 768) {
    $('p').addClass('hyphenate');
    Hyphenator.config({
          displaytogglebox : true,
          minwordlength : 4
      });
    Hyphenator.run();
  }
});
