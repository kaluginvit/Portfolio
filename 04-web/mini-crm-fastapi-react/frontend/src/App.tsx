import { Navigate, RouterProvider, createBrowserRouter, createHashRouter } from 'react-router-dom'
import AppLayout from './layout/AppLayout'
import ClientsPage from './pages/ClientsPage'
import DealsPage from './pages/DealsPage'
import SettingsPage from './pages/SettingsPage'
import TasksPage from './pages/TasksPage'

const routes = [
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/clients" replace /> },
      { path: 'clients', element: <ClientsPage /> },
      { path: 'deals', element: <DealsPage /> },
      { path: 'tasks', element: <TasksPage /> },
      { path: 'settings', element: <SettingsPage /> },
    ],
  },
]

const IS_DEMO = import.meta.env.VITE_DEMO_MODE === 'true'
const router = IS_DEMO ? createHashRouter(routes) : createBrowserRouter(routes)

export default function App() {
  return <RouterProvider router={router} />
}
