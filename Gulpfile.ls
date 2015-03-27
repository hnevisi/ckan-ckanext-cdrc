gulp = require \gulp
less = require \gulp-less

tinylr = require \tiny-lr

port = 35729

gulp.task \livereload !->
  tinylr := (require \tiny-lr)()
  tinylr.listen port

notify-lr = (e) !->
  fileName = require \path .relative(__dirname, e.path)
  tinylr.changed body: files: fileName

compile-css = (e) ->
  gulp.src './ckanext/cdrc/public/less/main.less'
    .pipe less!
    .pipe gulp.dest './ckanext/cdrc/fanstatic/css'

update = (e) !->
  compile-css e
  notify-lr e

gulp.task \watch, [\livereload], !->
  gulp.watch '**/*.css', update
  gulp.watch '**/*.less', update
  gulp.watch '**/*.html', update

gulp.task \less, ->
  compile-css


gulp.task \default, [\watch]
