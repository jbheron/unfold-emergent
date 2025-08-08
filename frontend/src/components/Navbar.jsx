import { NavLink } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="nav-bar">
      <div className="nav-inner">
        <div className="brand">
          <a href="/" className="brand-link">Unfold</a>
        </div>
        <div className="links">
          <NavLink to="/" end className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>Dashboard</NavLink>
          <NavLink to="/story" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>My Story</NavLink>
          <NavLink to="/coach" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>Coach</NavLink>
        </div>
      </div>
    </nav>
  );
}