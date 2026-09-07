import {
  AppBar,
  Box,
  Button,
  Container,
  Toolbar,
  Typography,
} from '@mui/material'
import { Link as RouterLink, Outlet } from 'react-router-dom'

const linkSx = { color: 'inherit', textDecoration: 'none', mx: 1 }
const IS_DEMO = import.meta.env.VITE_DEMO_MODE === 'true'

export default function AppLayout() {
  return (
    <Box sx={{ flexGrow: 1, minHeight: '100vh', bgcolor: 'grey.50' }}>
      {IS_DEMO && (
        <Box
          sx={{
            background: '#fff8e1',
            borderBottom: '2px solid #f9c920',
            py: 0.75,
            px: 2,
            textAlign: 'center',
            fontSize: 13,
            fontWeight: 600,
            color: '#5c3a00',
          }}
        >
          Demo Mode — synthetic data only · Google integration disabled · changes reset on page reload
        </Box>
      )}
      <AppBar position="static" color="primary" enableColorOnDark>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Мини-CRM {IS_DEMO ? '(Demo)' : '(учебный кейс)'}
          </Typography>
          <Button component={RouterLink} to="/clients" sx={linkSx}>
            Клиенты
          </Button>
          <Button component={RouterLink} to="/deals" sx={linkSx}>
            Сделки
          </Button>
          <Button component={RouterLink} to="/tasks" sx={linkSx}>
            Задачи
          </Button>
          <Button component={RouterLink} to="/settings" sx={linkSx}>
            Настройки Google
          </Button>
        </Toolbar>
      </AppBar>
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Outlet />
      </Container>
    </Box>
  )
}
