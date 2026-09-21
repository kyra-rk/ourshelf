import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

function NavMenu() {
  const [open, setOpen] = useState(false)
  const containerRef = useRef(null)

  useEffect(() => {
    function handleOutsideClick(event) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleOutsideClick)
    return () => document.removeEventListener('mousedown', handleOutsideClick)
  }, [])

  return (
    <div className="nav-menu" ref={containerRef}>
      <button
        type="button"
        className="nav-menu-trigger"
        onClick={() => setOpen((value) => !value)}
        aria-label="Open navigation menu"
        aria-expanded={open}
      >
        <span />
        <span />
        <span />
      </button>
      {open ? (
        <nav className="nav-menu-dropdown">
          <Link to="/" onClick={() => setOpen(false)}>
            Genres
          </Link>
          <Link to="/people" onClick={() => setOpen(false)}>
            Reader Profiles
          </Link>
        </nav>
      ) : null}
    </div>
  )
}

export default NavMenu
