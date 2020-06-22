import React, { useState, useEffect } from "react";
import { makeStyles } from '@material-ui/core/styles';
import { getSimulations, deleteSimulation, getMe } from '../../helpers/api';
import { Link } from 'react-router-dom'
import Button from "@material-ui/core/Button";
import Card from '@material-ui/core/Card';
import CardActionArea from '@material-ui/core/CardActionArea';
import CardActions from '@material-ui/core/CardActions';
import CardContent from '@material-ui/core/CardContent';
import CardMedia from '@material-ui/core/CardMedia';
import Typography from '@material-ui/core/Typography';
import IconButton from '@material-ui/core/IconButton';
import DeleteIcon from '@material-ui/icons/Delete';
import EditIcon from '@material-ui/icons/Edit';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogTitle from '@material-ui/core/DialogTitle';
import CircularProgress from '@material-ui/core/CircularProgress';

const useStyles = makeStyles((theme) => ({
  root: {
    flexGrow: 1,
  },
  container: {
    display: 'flex',
    flexWrap: 'wrap'
  },
  createSimulation: {
    marginBottom: 32
  },
  card: {
    width: 280,
    marginRight: 16,
    marginBottom: 16
  },
  cardMedia: {
    height: 140,
  },
  cardActions: {
    display: 'flex',
    justifyContent: 'flex-end'
  },
  details: {
    display: 'flex',
    alignItems: 'baseline',
    color: theme.palette.text.secondary
  },
  detailKey: {
    width: 64,
    fontWeight: 500,
    display: 'flex',
  },
}));


function SimulationCardContent({ simulation }) {
  const classes = useStyles();
  return (
    <React.Fragment>
      <CardMedia
        className={classes.cardMedia}
        image={simulation.image_url}
        title={simulation.name}
      />
      <CardContent>
        <Typography gutterBottom variant="h5" component="h2">
          {simulation.name}
        </Typography>
        <div className={classes.details}>
          <Typography className={classes.detailKey} variant="body2">Author:</Typography>
          <Typography variant="body2">{simulation.author}</Typography>
        </div>
        <div className={classes.details}>
          <Typography className={classes.detailKey} variant="body2">Citation:</Typography>
          <Typography variant="body2">{simulation.citation}</Typography>
        </div>
        <div className={classes.details}>
          <Typography className={classes.detailKey} variant="body2">Runner:</Typography>
          <Typography variant="body2">{simulation.runner}</Typography>
        </div>
        <Typography variant="body2" color="textSecondary" component="p">
          {simulation.description}
        </Typography>
      </CardContent>
    </React.Fragment>
  )
}


const SimulationList = () => {
  const classes = useStyles();
  const [loading, setLoading] = useState(true);
  const [simulationList, setSimulationList] = useState([]);
  const [deletingSimulation, setDeletingSimulation] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [manager, setManager] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const result = await getSimulations();
        setSimulationList(result.items);
        const me = await getMe();
        setManager(!!me.can_manage_simulations);
      } catch (e) {
        console.log(e);
      }
      setLoading(false);
    })();
  }, []);

  const handleDeleteDialogOpen = (simulation) => {
    setDeletingSimulation(simulation);
  };

  const handleDeleteDialogClose = async (confirm) => {
    setDeleting(true);
    if (confirm) {
      try {
        await deleteSimulation(deletingSimulation.id);
        const result = await getSimulations();
        setSimulationList(result.items);
      } catch (e) {
        console.log(e);
      }
    }
    setDeleting(false);
    setDeletingSimulation(null);
  };

  return (
    loading ?
    <CircularProgress />
    :
    <div className={classes.root}>
      {manager && 
        <Button
          color="primary"
          variant="contained"
          className={classes.createSimulation}
          component={Link}
          to="/simulations/create"
        >
          Add a simulation
        </Button>
      }
      <div className={classes.container}>
        {simulationList.map((simulation) =>
          <Card className={classes.card} key={simulation.id}>
            {manager ? 
              <CardActionArea component={Link} to={`/simulations/${simulation.id}`} >
                <SimulationCardContent simulation={simulation} />
              </CardActionArea>
            : 
              <SimulationCardContent simulation={simulation} />
            }
            {manager &&
              <CardActions className={classes.cardActions}>
                <IconButton component={Link} to={`/simulations/${simulation.id}`} >
                  <EditIcon />
                </IconButton>
                <IconButton onClick={() => handleDeleteDialogOpen(simulation)} >
                  <DeleteIcon />
                </IconButton>
              </CardActions>
          }
          </Card>
        )}
      </div>
      <Dialog
        open={deletingSimulation != null}
        onClose={() => handleDeleteDialogClose(false)}
      >
        <DialogTitle>Are you sure you want to delete this simulation?</DialogTitle>
        <DialogActions>
          <Button onClick={() => handleDeleteDialogClose(false)} color="secondary" disabled={deleting}>
            Cancel
          </Button>
          <Button onClick={() => handleDeleteDialogClose(true)} color="primary" autoFocus disabled={deleting}>
            Yes
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  )
}

export default SimulationList;