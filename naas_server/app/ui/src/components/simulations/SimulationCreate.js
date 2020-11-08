import React, { useState, useEffect } from "react";
import { firestorage } from "../../helpers/firebase";
import { useHistory, useParams } from "react-router-dom";
import { makeStyles } from '@material-ui/core/styles';
import { createSimulation, updateSimulation, getSimulation } from '../../helpers/api';
import Button from "@material-ui/core/Button";
import FormControl from "@material-ui/core/FormControl";
import InputLabel from "@material-ui/core/InputLabel";
import Select from "@material-ui/core/Select";
import TextField from '@material-ui/core/TextField';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import Checkbox from '@material-ui/core/Checkbox';
import CircularProgress from '@material-ui/core/CircularProgress';
import Snackbar from '@material-ui/core/Snackbar';
import Alert from '@material-ui/lab/Alert';

const useStyles = makeStyles(() => ({
  root: {
    flexGrow: 1
  },
  form: {
    display: 'flex',
    flexFlow: 'column'
  },
  formControl: {
    marginBottom: 16,
  },
  formSelect: {
    paddingTop: 16
  },
  fileInput: {
    display: 'flex',
    alignItems: 'center',
    marginBottom: 16
  },
  chooseFileButton: {
    minWidth: 180,
  },
  chooseFileOr: {
    padding: '0 24px'
  },
  chooseFileUrl: {
    flexGrow: 1
  },
  image: {
    maxWidth: 400,
    maxHeight: 400,
    marginBottom: 16
  },
  submit: {
    marginTop: 8,
    marginBottom: 8
  }
}));

const SimulationFileInput = ({ id, text, url, accept, onChange, uploadProgress, allowManualUrl }) => {
  const classes = useStyles();

  return (
    <div className={classes.fileInput}>
      <input
        accept={accept}
        style={{ display: 'none' }}
        id={id}
        type="file"
        onChange={onChange}
      />
      <label htmlFor={id}>
        <Button 
          variant="outlined" 
          component="span" 
          className={classes.chooseFileButton}
          disabled={!!uploadProgress}
        >
          {uploadProgress ? `${uploadProgress}%` : `${text}`}
        </Button>
      </label>
      {allowManualUrl &&
      <>
        <div className={classes.chooseFileOr}>or enter URL</div>
        <TextField
            variant="outlined"
            label="URL"
            defaultValue={url}
            key={url}
            className={classes.chooseFileUrl}
            onChange={onChange}
          />
      </>
      }
    </div>
  )
}


const SimulationCreate = () => {
  const classes = useStyles();
  const { simulationId } = useParams();
  const history = useHistory();
  const [simulation, setSimulation] = useState({
    runner: '',
    public: false
  });
  const [submitting, setSubmitting] = useState(false);
  const [uploadImageProgress, setUploadImageProgress] = useState(null);
  const [uploadConfigProgress, setUploadConfigProgress] = useState(null);
  const [uploadTopologyProgress, setUploadTopologyProgress] = useState(null);
  const [uploadTrajectoryProgress, setUploadTrajectoryProgress] = useState(null);
  const [uploadRenderingProgress, setUploadRenderingProgress] = useState(null);
  const [loading, setLoading] = useState(!!simulationId);
  const [snackbarMessage, setSnackbarMessage] = useState(null);

  useEffect(() => {
    (async () => {
      if (simulationId) {
        try {
          const result = await getSimulation(simulationId);
          setSimulation(result);
        } catch (e) {
          window.Rollbar.warning(e);
          console.log(e);
        }
        setLoading(false);
      };
    })();
  }, [simulationId]);

  const random_six_digits = () => {
    return Math.floor(100000 + Math.random() * 900000);
  }

  const updateSimulationFile = (e, onUpdateProgress, onDownloadUrl) => {
    if (!e.target.files) {
      onDownloadUrl(e.currentTarget.value);
    } else {
      onUpdateProgress(0);
      const f = e.target.files[0];
      const uploadRef = firestorage().ref(`/simulations/${random_six_digits()}_${f.name}`);
      uploadRef.put(f).on('state_changed', snapshot => {
        const progress = Math.round(100 * snapshot.bytesTransferred / snapshot.totalBytes);
        onUpdateProgress(progress);
      }, e => {
        window.Rollbar.warning(e);
        console.log(e);
        onUpdateProgress(null);
      }, () => {
        uploadRef.getDownloadURL().then(url => {
          onDownloadUrl(url);
          onUpdateProgress(null);
        });
      });
    }
  }

  const onChangeDescription = e => {
    setSimulation({...simulation, description: e.currentTarget.value});
  }

  const onChangeName = e => {
    setSimulation({...simulation, name: e.currentTarget.value});
  }

  const onChangeAuthor = e => {
    setSimulation({...simulation, author: e.currentTarget.value});
  }

  const onChangeCitation = e => {
    setSimulation({...simulation, citation: e.currentTarget.value});
  }

  const onChangeRunner = e => {
    setSimulation({...simulation, runner: e.currentTarget.value});
  }

  const onChangeImage = e => {
    updateSimulationFile(e, setUploadImageProgress, url => setSimulation({...simulation, image_url: url}));
  }

  const onChangeConfig = e => {
    updateSimulationFile(e, setUploadConfigProgress, url => simulation.config_url = url);
  }

  const onChangeTopology = e => {
    updateSimulationFile(e, setUploadTopologyProgress, url => setSimulation({...simulation, topology_url: url}));
  }

  const onChangeTrajectory = e => {
    updateSimulationFile(e, setUploadTrajectoryProgress, url => setSimulation({...simulation, trajectory_url: url}));
  }

  const onChangeRendering = e => {
    updateSimulationFile(e, setUploadRenderingProgress, url => setSimulation({...simulation, rendering_url: url}));
  }

  const onChangePublic = e => {
    setSimulation({...simulation, public: e.currentTarget.checked});
  }

  const onSubmit = async e => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (simulationId) {
        await updateSimulation(simulation);
      } else {
        await createSimulation(simulation);
      }
      history.push('/simulations');
    } catch (e) {
      window.Rollbar.warning(e);
      console.log(e);
      setSubmitting(false);
      setSnackbarMessage(e.response.data.message);
    }
  };
  
  const onCancel = () => {
    history.push('/simulations');
  };

  return (
    loading ?
      <CircularProgress/>
    :
    <div className={classes.root}>
      <form noValidate className={classes.form}>
        <TextField
          variant="outlined"
          label="Name"
          defaultValue={simulation.name}
          onChange={onChangeName}
          className={classes.formControl}
          required
        />
        <TextField
          variant="outlined"
          label="Description"
          defaultValue={simulation.description}
          onChange={onChangeDescription}
          className={classes.formControl}
        />
        <TextField
          variant="outlined"
          label="Author"
          defaultValue={simulation.author}
          onChange={onChangeAuthor}
          className={classes.formControl}
        />
        <TextField
          variant="outlined"
          label="Citation"
          defaultValue={simulation.citation}
          onChange={onChangeCitation}
          className={classes.formControl}
        />        
        <FormControlLabel 
          variant="outlined" 
          className={classes.formControl}
          control={
            <Checkbox
              defaultChecked={simulation.public}
              onChange={onChangePublic}
              color="primary"
            />
          }
          label="Public"
        />
        {simulation.image_url && 
          <img 
            src={simulation.image_url} 
            className={classes.image} 
            alt={simulation.name}
          />
        }
        <SimulationFileInput 
          id="image-input"
          text="Choose thumbnail"
          accept="image/*"
          onChange={onChangeImage}
          uploadProgress={uploadImageProgress}
        />
        <FormControl variant="outlined" className={classes.formControl} required>
          <InputLabel>Runner</InputLabel>
          <Select
            native
            defaultValue={simulation.runner}
            onChange={onChangeRunner}
            label="Runner"
          >
            <option disabled value=''></option>
            <option value='ase'>ASE</option>
            <option value='omm'>OMM</option>
            <option value='static'>Static</option>
            <option value='trajectory'>Trajectory</option>
          </Select>
        </FormControl>
        {(simulation.runner === 'ase' || simulation.runner === 'omm') &&
          <SimulationFileInput 
            id="config-input"
            text="Choose config"
            url={simulation.config_url}
            accept="*/*"
            onChange={onChangeConfig}
            uploadProgress={uploadConfigProgress}
            allowManualUrl={true}
          />
        }
        {(simulation.runner === 'trajectory' || simulation.runner === 'static') &&
          <SimulationFileInput 
            id="topology-input"
            text="Choose topology"
            url={simulation.topology_url}
            accept="*/*"
            onChange={onChangeTopology}
            uploadProgress={uploadTopologyProgress}
            allowManualUrl={true}
          />
        }
        {simulation.runner === 'trajectory' &&
          <SimulationFileInput 
            id="trajectory-input"
            text="Choose trajectory"
            url={simulation.trajectory_url}
            accept="*/*"
            onChange={onChangeTrajectory}
            uploadProgress={uploadTrajectoryProgress}
            allowManualUrl={true}
          />
        }
        {false &&
          <SimulationFileInput 
            id="rendering-input"
            text="Choose rendering"
            url={simulation.rendering_url}
            accept="*/*"
            onChange={onChangeRendering}
            uploadProgress={uploadRenderingProgress}
            allowManualUrl={true}
          />
        }
        <Button 
          type="submit"
          color="primary"
          variant="contained"
          onClick={onSubmit}
          className={classes.submit}
          disabled={submitting || !!uploadImageProgress || !!uploadConfigProgress || !!uploadTopologyProgress}
        >
          {simulationId ? 'Save' : 'Add'}
        </Button>
        <Button 
          variant="outlined"
          onClick={onCancel}
          disabled={submitting}
        >
          Cancel
        </Button>
      </form>
      <Snackbar 
        open={!!snackbarMessage} 
        autoHideDuration={6000} 
        onClose={() => setSnackbarMessage(null)} 
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}>
          <Alert 
            onClose={() => setSnackbarMessage(null)} 
            severity="error">
              {snackbarMessage}
          </Alert>
      </Snackbar>
    </div>
  )
}

export default SimulationCreate;