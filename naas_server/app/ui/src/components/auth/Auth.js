import React, { useState } from "react";
import { Link } from 'react-router-dom'
import GoogleButton from 'react-google-button'
import Footer from '../Footer';
import { makeStyles } from '@material-ui/core/styles';
import { login, loginWithGoogle, register } from "../../helpers/auth";
import { createUser, getMe } from "../../helpers/api";
import { fireauth } from '../..//helpers/firebase';
import TextField from "@material-ui/core/TextField"
import Button from "@material-ui/core/Button"
import narupaLogo from '../../images/narupa-192.png';
import Typography from '@material-ui/core/Typography';

const useStyles = makeStyles((theme) => ({
  root: {
    display: 'flex',
    flexFlow: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    width: 500,
    margin: '120px auto 64px auto',
    padding: '32px 0',
    backgroundColor: 'rgba(0, 0, 0, 0.02)',
    borderRadius: 16
  },
  container: {
    display: 'flex',
    flexFlow: 'column',
    width: 400
  },
  title: {
    marginBottom: 16
  },
  form: {
    display: 'flex',
    flexFlow: 'column'
  },
  input: {
    marginBottom: 16
  },
  or: {
    display: 'flex',
    justifyContent: 'center'
  },
  error: {
    display: 'flex',
    justifyContent: 'center',
    marginBottom: 16,
    color: 'red'
  },
  footer: {
    display: 'flex',
    marginTop: 16
  },
  link: {
    marginLeft: 4,
    color: '#ff6600'
  },
  googleButtonContainer: {
    display: 'flex',
    justifyContent: 'center',
    marginBottom: 32
  }
}));

const Auth = ({ registering = false }) => {
  const classes = useStyles();
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const onSubmitEmailAndPassword = async e => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (registering) {
        const firebaseResponse = await register(email, password);
        await createUser(firebaseResponse.user, name);
        await fireauth().currentUser.getIdToken(true);
      } else {
        await login(email, password);
      }
    } catch (e) {
      console.log(e);
      setError(`There was a problem. ${e.message}`);
      setSubmitting(false);
    }
  }

  const onSubmitGoogle = async e => {
    if (registering) {
      e.preventDefault();
      setError(null);
      setSubmitting(true);
      try {
        const firebaseResponse = await loginWithGoogle();
        await createUser(firebaseResponse.user, name);
        await fireauth().currentUser.getIdToken(true);
      } catch (e) {
        console.log(e);
        setError(`There was a problem. ${e.message}`);
        setSubmitting(false);
      }
    } else {
      await loginWithGoogle();
      try {
        await getMe();
      } catch (e) {
        setError('Could not find a login for your Google account. Do you need to register?');
      }
    }
  }

  const onChangeEmail = e => {
    setEmail(e.currentTarget.value);
  }

  const onChangePassword = e => {
    setPassword(e.currentTarget.value);
  }

  const onChangeName = e => {
    setName(e.currentTarget.value);
  }

  return (
    <div className={classes.root}>
      <img src={narupaLogo} alt="narupa"/>
      <Typography variant="h6" className={classes.title}>
        {registering ? 'Register' : 'Login'}
      </Typography>
      <div className={classes.container}>
        {error !== null && <div className={classes.error}>{error}</div>}
        <form className={classes.form}>
          {registering && 
            <TextField
              type="text"
              variant="outlined"
              label="Name"
              className={classes.input}
              value={name}
              onChange={onChangeName}
            />
          }
          <TextField
            type="email"
            variant="outlined"
            label="Email"
            className={classes.input}
            value={email}
            onChange={onChangeEmail}
          />
          <TextField
            type="password"
            variant="outlined"
            label="Password"
            className={classes.input}
            value={password}
            onChange={onChangePassword}
          />
          <Button 
            type="submit"
            color="primary"
            variant="contained"
            disabled={submitting}
            onClick={onSubmitEmailAndPassword}
          >
            {registering ? 'Register' : 'Login'}
          </Button>
        </form>
        <p className={classes.or}>or</p>
          <div className={classes.googleButtonContainer}>
          <GoogleButton 
            type="light"
            disabled={submitting}
            onClick={onSubmitGoogle}
            className={classes.googleButton}
            label={registering ? 'Register with Google' : 'Login with Google'}
          />
        </div>
        <div className={classes.footer}>
          {registering && 
          <>
            <div>Already have an account?</div>
            <Link to="/login" className={classes.link}>Login here</Link>
          </>
          }
          {!registering && 
          <>
            <div>Don't have an account?</div>
            <Link to="/register" className={classes.link}>Register here</Link>
          </>
          }
        </div>
      </div>
      <Footer/>
    </div>
  );
};

export default Auth;
