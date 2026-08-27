import { HttpInterceptorFn } from '@angular/common/http';

export const correlationInterceptor: HttpInterceptorFn = (req, next) => {
  const correlationId = crypto.randomUUID();
  const trackedReq = req.clone({
    setHeaders: {
      'X-Correlation-Id': correlationId
    }
  });
  return next(trackedReq);
};
