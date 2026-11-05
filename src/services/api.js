/**
 * API service for the FastAPI backend (back-end/).
 * In development: Vite proxies /api/* → http://localhost:8000/* (see vite.config.js)
 * In production:  set VITE_API_URL to the FastAPI origin.
 */

const BASE = import.meta.env.VITE_API_URL || '/api'

async function request(path) {
  const res = await fetch(`${BASE}${path}`)

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    // FastAPI errors are { detail: string } or { detail: [{ msg }] } for validation errors
    const detail = Array.isArray(body.detail) ? body.detail[0]?.msg : body.detail
    throw new Error(detail || `Request failed: ${res.status}`)
  }

  return res.json()
}

/**
 * Search stops by name. Returns [{ id, point_name }].
 * GET /route-points/?q=<query>
 */
export async function searchLocations(query) {
  return request(`/route-points/?q=${encodeURIComponent(query)}`)
}

/**
 * Find the fare between two stops. `from` and `to` are stops from searchLocations.
 * GET /fair/routes?start_point_id=&end_point_id=
 *
 * The backend returns every route that connects both stops; the cheapest one with a
 * known fare is shown.
 */
export async function calculateFare({ from, to, transport, passengerType }) {
  const params = new URLSearchParams({ start_point_id: from.id, end_point_id: to.id })
  const routes = await request(`/fair/routes?${params}`)

  if (routes.length === 0) {
    throw new Error('No jeepney route connects these two stops yet.')
  }

  const priced = routes.filter((r) => r.regular_fare !== null)
  if (priced.length === 0) {
    throw new Error('The fare for this route is not available yet. Please try again later.')
  }

  const route = priced.reduce((a, b) => (b.regular_fare < a.regular_fare ? b : a))
  const discounted = passengerType !== 'Regular'
  const total = discounted ? route.discounted_fare : route.regular_fare

  return {
    from: from.point_name,
    to: to.point_name,
    transport,
    passengerType,
    routeName: route.route_name,
    stops: route.points.length,
    distance: route.distance_km,
    regularFare: route.regular_fare,
    discountAmount: discounted ? route.regular_fare - route.discounted_fare : 0,
    total,
  }
}
