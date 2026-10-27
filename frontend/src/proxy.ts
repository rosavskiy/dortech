import { NextResponse, type NextRequest } from "next/server";
/** Кабинеты требуют cookie сессии; само содержимое проверяется на сервере по /auth/me. */
export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if ((pathname.startsWith("/account") || pathname.startsWith("/manager")) && !request.cookies.get("dt_session")) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}
export const config = { matcher: ["/account/:path*", "/manager/:path*"] };
