// Domain types mirroring backend schemas

export type PlatformRole = 'platform_admin' | 'case_owner' | 'case_investigator' | 'case_reviewer';
export type CaseRole = 'case_owner' | 'case_investigator' | 'case_reviewer';
export type EvidenceStatus = 'PENDING' | 'PARSING' | 'PARSED' | 'PARSE_FAILED' | 'UNSUPPORTED';
export type ArtifactType =
  | 'EXTRACTED_TEXT'
  | 'OCR_TEXT'
  | 'EMAIL_HEADERS'
  | 'EMAIL_BODY'
  | 'SPREADSHEET_TEXT'
  | 'RAW_METADATA';
export type AuditEventType =
  | 'USER_REGISTERED'
  | 'USER_LOGIN'
  | 'USER_LOGIN_FAILED'
  | 'USER_MFA_ENABLED'
  | 'USER_LOGOUT'
  | 'CASE_CREATED'
  | 'CASE_UPDATED'
  | 'CASE_ARCHIVED'
  | 'MEMBER_ADDED'
  | 'MEMBER_REMOVED'
  | 'MEMBER_ROLE_CHANGED'
  | 'EVIDENCE_UPLOADED'
  | 'EVIDENCE_PARSED'
  | 'EVIDENCE_PARSE_FAILED'
  | 'EVIDENCE_VIEWED'
  | 'EVIDENCE_DOWNLOADED'
  | 'AUDIT_VERIFIED';

export interface User {
  id: string;
  email: string;
  platform_role: PlatformRole;
}

export interface Case {
  id: string;
  name: string;
  description: string | null;
  status: 'active' | 'archived';
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface CaseMember {
  id: string;
  case_id: string;
  user_id: string;
  case_role: CaseRole;
  added_at: string;
}

export interface Evidence {
  id: string;
  case_id: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  sha256_hash: string;
  status: EvidenceStatus;
  description: string | null;
  tags: string[];
  uploaded_at: string;
  parsed_at: string | null;
}

export interface Artifact {
  id: string;
  evidence_id: string;
  artifact_type: ArtifactType;
  content: string | null;
  metadata_: Record<string, unknown>;
  created_at: string;
}

export interface AuditLogEntry {
  id: string;
  prev_hash: string;
  event_type: AuditEventType;
  actor_id: string | null;
  case_id: string | null;
  subject_id: string | null;
  payload: Record<string, unknown>;
  created_at: string;
  entry_hash: string;
}

export interface AuditVerifyResult {
  valid: boolean;
  total_entries: number;
  first_entry_id: string | null;
  last_entry_id: string | null;
  error: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
