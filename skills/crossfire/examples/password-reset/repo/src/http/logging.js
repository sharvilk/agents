// Access log: one line per request, shipped to the log store and kept for 90 days.
export function accessLog(req, res, next) {
  const started = Date.now();
  res.on('finish', () => {
    console.log(JSON.stringify({
      method: req.method,
      url: req.originalUrl,
      status: res.statusCode,
      ms: Date.now() - started,
      ip: req.ip
    }));
  });
  next();
}
