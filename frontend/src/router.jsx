import { Link, Route, Router, Switch, useLocation, useParams, useSearchParams } from 'wouter';

export { Link, Route, useParams, useSearchParams };
export const BrowserRouter = Router;
export const Routes = Switch;

export function useNavigate() {
  const [, navigate] = useLocation();
  return navigate;
}

export function NavLink({ to, end = false, className = '', children, ...props }) {
  const [location] = useLocation();
  const active = end ? location === to : location === to || location.startsWith(`${to}/`);
  const resolvedClassName = typeof className === 'function'
    ? className({ isActive: active })
    : [className, active ? 'active' : ''].filter(Boolean).join(' ');

  return (
    <Link href={to} className={resolvedClassName} aria-current={active ? 'page' : undefined} {...props}>
      {children}
    </Link>
  );
}
