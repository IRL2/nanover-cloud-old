import React, { useState, useEffect } from "react";
import { Route, BrowserRouter, Redirect, Switch} from 'react-router-dom'
import { fireauth } from './helpers/firebase';
import Auth from "./components/auth/Auth";
import SessionList from "./components/sessions/SessionList";
import SessionCreate from "./components/sessions/SessionCreate";
import SimulationList from "./components/simulations/SimulationList";
import SimulationCreate from "./components/simulations/SimulationCreate";
import Account from "./components/account/Account";
import CssBaseline from '@material-ui/core/CssBaseline';
import Main from "./components/Main";
import { createMuiTheme, ThemeProvider } from '@material-ui/core/styles';

const theme = createMuiTheme({
  palette: {
    primary: {
      main: '#ff6600',
      contrastText: '#fff'
    },
    secondary: {
      main: '#bbb'
    }
  },
});

function PrivateRoute ({component, authed, breadcrumbs, ...rest}) {
  return (
    <Route
      {...rest}
      render={(props) => authed === true
        ? <Main component={component} props={props} breadcrumbs={breadcrumbs} />
        : <Redirect to={{pathname: '/login', state: {from: props.location}}} />}
    />
  )
}

function PublicRoute ({component: Component, authed, componentProps, ...rest}) {
  return (
    <Route
      {...rest}
      render={(props) => authed === false
        ? <Component {...props} {...componentProps} />
        : <Redirect to='/sessions' />}
    />
  )
}

const App = () => {
  const [loading, setLoading] = useState(true);
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    return fireauth().onAuthStateChanged((firebaseUser) => {
      setAuthed(!!firebaseUser);
      setLoading(false);
    });
  }, []);

  return (
    loading ? <React.Fragment/> : (
      <ThemeProvider theme={theme}>
        <CssBaseline/>
        <BrowserRouter>
          <Switch>
            <PublicRoute 
              authed={authed} 
              path='/login' 
              component={Auth}
            />
            <PublicRoute 
              authed={authed} 
              path='/register' 
              component={Auth}
              componentProps={{ 
                registering: true 
              }}
            />
            <PrivateRoute 
              authed={authed} 
              breadcrumbs={[{text: 'Simulations', path: '/simulations'}, {text: 'Add'}]}
              path='/simulations/create' 
              component={SimulationCreate}
            />
            <PrivateRoute 
              authed={authed} 
              breadcrumbs={[{text: 'Simulations', path: '/simulations'}, {text: 'Edit'}]}
              path='/simulations/:simulationId' 
              component={SimulationCreate}
            />
            <PrivateRoute 
              authed={authed} 
              breadcrumbs={[{text: 'Simulations'}]}
              path='/simulations'
              component={SimulationList} 
            />
            <PrivateRoute 
              authed={authed} 
              breadcrumbs={[{text: 'Sessions', path: '/sessions'}, {text: 'Schedule'}]}
              path='/sessions/create' 
              component={SessionCreate} 
            />
            <PrivateRoute 
              authed={authed} 
              breadcrumbs={[{text: 'Sessions', path: '/sessions'}, {text: 'Edit'}]}
              path='/sessions/:sessionId' 
              component={SessionCreate} 
            />
            <PrivateRoute 
              authed={authed} 
              breadcrumbs={[{text: 'Sessions'}]}
              path='/sessions' 
              component={SessionList} 
            />
            <PrivateRoute 
              authed={authed} 
              breadcrumbs={[{text: 'Account'}]}
              path='/account' 
              component={Account} 
            />
            <Redirect from='/' to='/sessions'/>
          </Switch>
        </BrowserRouter>
      </ThemeProvider>
    )
  )
      
}

export default App;