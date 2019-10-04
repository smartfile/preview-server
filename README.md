![CI status](https://travis-ci.org/btimby/django-proxysql.png "CI Status")

# preview-server

A docker container to produce PNG image previews for common file types. This container is intended to be used as part of a larger application stack.

The container uses circusd to execute and monitor a Python async http server that is the main service as well as `soffice.bin` (via `unoconv`) which is used for office document conversion. The preview service also utilizes `ffmpeg`, `ghostscript` and `imagemagick`.

The focus of this project is to provide a preview success rate as close as possible to 100%. This is achieved by careful testing and error handling. For example, `soffice.bin` will be restarted if it consumes too much memory. Also, the preview service will retry requests to `soffice.bin` in order to recover from conversion errors.

## Usage

You should pull the latest stable image from DockerHub and run it like this:

```bash
docker pull btimby/preview-server
docker run -p 3000:3000 -ti btimby/preview-server
```

Once the service has initialised, files, paths, or urls can be sent to the `/preview/` endpoint, and a PNG preview will be returned. Additional configuration is necessary in order to use paths, see Options below for more information. Optional `width` and `height` arguments can be sent with the request to control the size of the returned preview image.

```bash
curl -o out.png -F 'file=@mydoc.doc' http://localhost:3000/preview/
curl -o out.png -F 'url=http://somedomain.com/some-pdf' http://localhost:3000/preview/
curl -o out-small.png -F 'width=100' -F 'height=50' -F 'file=@mydoc.doc' http://localhost:3000/preview/
```

## Options

A number of features are controlled by environment variables.

`PVS_FILES` - This option informs the preview service where files are located. When enabled, the service can be sent a path rather than a file body. The provided path is used relative to `PVS_FILES`.

For example, below the file located at `/mnt/files/path/to/file.doc` will be previewed.

```bash
docker run -d -p 3000:3000 --tmpfs /tmp \
    -v /mnt/files:/mnt/files -e PVS_FILES=/mnt/files \
    btimby/preview-server
curl -o out.png -F 'path=/path/to/file.doc' \
    -F 'width=200' -F 'height=100' http://localhost:3000/preview/
```

`PVS_CACHE_CONTROL` - This option controls the `Cache-Control` header emitted by the service. When omitted, the header supressed. When present, it controls the number of minutes previews should be cached.

`PVS_STORE` - By default generated previews are ephemeral. If you wish to store the previews so that they are not regenerated in future requests, you can do so using ththis option.

This can be used as a cache mechanism, for example by using tmpfs. Optionally, you can provide a file system (even a shared file system) for long-term storage. When combined with `PVS_FILES`, The file's mtime is compared to the preview's mtime. If the source file is newer, the preview is regenerated. This option has no effect for POSTed or downloaded files.

For example, below the host's `/mnt/store` directory or device will be used to store generated previews. The second call to `curl` will be much faster as it will simply return the preview generated in the first call.

```bash
docker run -d -p 3000:3000 --tmpfs /tmp \
    -v /mnt/files:/mnt/files -e PVS_FILES=/mnt/files \
    -v /mnt/store:/mnt/store -e PVS_STORE=/mnt/store \
    btimby/preview-server
curl -o out.png -F 'path=/path/to/file.doc' http://localhost:3000/preview/
curl -o out.png -F 'path=/path/to/file.doc' http://localhost:3000/preview/
```

`PVS_DEFAULT_WIDTH` & `PVS_DEFAULT_HEIGHT` - These options provide the default width and height of generated PNG previews. If the caller omits `width` and `height` parameters to the service, these defaults are used.

`PVS_MAX_WIDTH` & `PVS_MAX_HEIGHT` - These options provide the maximum allowable `width` and `height` that a user can request.

`PVS_LOGLEVEL` & `PVS_HTTP_LOGLEVEL` - These options control the log output generated by the preview service. The first applies to the service in general, the second to `aiohttp`'s access log.

While developing, you might increase `PVS_LOGLEVEL` to see details about the service operation, but lower `PVS_HTTP_LOGLEVEL`. During normal operation, the opposite may be more useful.

`PVS_METRICS` - Enable prometheus metrics at `/metrics/` endpoint.

`/tmp` - The preview service creates many small, short-lived temporary files. I recommend using Docker's `tmpfs` facility to eliminate the I/O involved in managing these files.

```bash
docker run -d -p 3000:3000 --tmpfs /tmp ...
```

## Development

To build, run:

```bash
docker build --rm -ti btimby/preview-server .
```

Once the service is initialized, you can test it using:

To run the stress testing tool `make test`
To use the interactive test: `make test.html`

## License

MIT, see `LICENSE`.
