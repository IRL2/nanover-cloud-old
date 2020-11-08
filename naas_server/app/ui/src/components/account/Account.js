import React, { useState, useEffect } from "react";
import { makeStyles } from '@material-ui/core/styles';
import { logout } from "../../helpers/auth";
import { getMe, updateMeZoom } from "../../helpers/api";
import { useQuery } from "../../helpers/utils";
import Button from "@material-ui/core/Button";
import Typography from "@material-ui/core/Typography";
import CircularProgress from "@material-ui/core/CircularProgress";

const useStyles = makeStyles((theme) => ({
  root: {
    flexGrow: 1,
    display: 'flex',
    flexFlow: 'column'
  },
  details: {
    display: 'flex',
    marginBottom: 16
  },
  detailKey: {
    width: 64,
    fontWeight: 500,
    display: 'flex',
    alignItems: 'center'
  },
  connectToZoom: {
    marginTop: 8,
    marginBottom: 16
  }
}));

const Account = () => {
  const classes = useStyles();
  const zoomAuthorizationCode = useQuery().get('code');
  const [loading, setLoading] = useState(true);
  const [me, setMe] = useState(null);
  const zoomRedirectUri = `${window.location.protocol}//${window.location.hostname}/account`;

  useEffect(() => {
    (async () => {
      try {
        if (zoomAuthorizationCode) {
          try {
            await updateMeZoom(zoomAuthorizationCode, zoomRedirectUri);
          } catch (e) {
            window.Rollbar.warning(e);
            console.log(e);
          }
        }
        const result = await getMe();
        setMe(result);
      } catch (e) {
        window.Rollbar.warning(e);
        console.log(e);
      }
      setLoading(false);
    })();
  }, [zoomAuthorizationCode, zoomRedirectUri]);

  return (
    loading || !me ?
      <CircularProgress />
    :
      <div className={classes.root}>
        <div className={classes.details}>
          <Typography className={classes.detailKey}>Name:</Typography>
          <Typography>{me.name}</Typography>
        </div>
        <div className={classes.details}>
          <Typography className={classes.detailKey}>Email:</Typography>
          <Typography>{me.email}</Typography>
        </div>
	{/*
        <div className={classes.details}>
          <Typography className={classes.detailKey}>Quota:</Typography>
          <Typography>{me.quota_hours_per_month} hours per month</Typography>
        </div>
        <div className={classes.details}>
          <Typography className={classes.detailKey}>Zoom:</Typography>
          <Typography>{(me.zoom && me.zoom.access_token) ? 'Connected' : 
          <Button
            variant="contained"
            color="primary"
            component="a"
            href={`https://zoom.us/oauth/authorize?response_type=code&client_id=QfpjF5n7RvWW68tqhsS5tA&redirect_uri=${encodeURIComponent(zoomRedirectUri)}`}
            className={classes.connectToZoom}
            >Connect to Zoom</Button>
          }</Typography>
        </div>
	*/}
        <div className={classes.details}>
          <Typography className={classes.detailKey}>&nbsp;</Typography>
          <Typography>
            <Button
              variant="contained"
              color="primary"
              onClick={logout}
              className={classes.logout}
            >
              Logout
            </Button>
          </Typography>
        </div>
        
      </div>
  );
};

export default Account;
