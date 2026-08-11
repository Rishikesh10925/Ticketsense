export function Loading({label="Loading..."}:{label?:string}){return <div className="state-card"><span className="spinner"/>{label}</div>}
export function ErrorState({message,onRetry}:{message:string;onRetry?:()=>void}){return <div className="state-card error-box"><b>Unable to load data.</b><span>{message}</span>{onRetry&&<button onClick={onRetry}>Try again</button>}</div>}
export function Empty({label="No tickets found."}:{label?:string}){return <div className="state-card">{label}</div>}
export function Badge({value}:{value?:string|null}){return <span className={`badge ${value==="urgent"||value==="escalated"?"rose":value==="high"?"amber":value==="resolved"?"green":value==="in_review"?"violet":"blue"}`}>{value?.replaceAll("_"," ")||"—"}</span>}
