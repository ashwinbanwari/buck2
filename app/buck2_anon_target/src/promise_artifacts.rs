/*
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under both the MIT license found in the
 * LICENSE-MIT file in the root directory of this source tree and the Apache
 * License, Version 2.0 found in the LICENSE-APACHE file in the root directory
 * of this source tree.
 */

use std::fmt;
use std::fmt::Debug;
use std::sync::Arc;
use std::sync::OnceLock;

use allocative::Allocative;
use buck2_build_api::artifact_groups::promise::PromiseArtifact;
use buck2_build_api::artifact_groups::promise::PromiseArtifactId;
use buck2_core::fs::paths::forward_rel_path::ForwardRelativePathBuf;
use dupe::Dupe;
use gazebo::prelude::SliceExt;
use starlark::codemap::FileSpan;
use starlark::values::Trace;

#[derive(Debug, Trace, Allocative)]
struct PromiseArtifactEntry {
    location: Option<FileSpan>,
    artifact: PromiseArtifact,
}

/// The PromiseArtifactRegistry stores promises registered with `artifact_promise_mappings` in `anon_rule()`, and their
/// corresponding internal PromiseArtifact. At the end of analysis (after promises have been resolved),
/// all PromiseArtifact will be updated to have the resolved artifact from the corresponding starlark promise.
#[derive(Debug, Trace, Allocative)]
pub(crate) struct PromiseArtifactRegistry {
    artifacts: Vec<PromiseArtifactEntry>,
}

impl PromiseArtifactRegistry {
    pub(crate) fn new() -> Self {
        Self {
            artifacts: Vec::new(),
        }
    }

    /// The consumer analysis is the analysis that calls the anon target and uses the resulting
    /// promised artifacts. It could be a normal rule analysis, an analysis from BXL, or an anon
    /// target analysis. These promised artifacts are the ones that will have their short paths
    /// asserted. During promise resolution, we use the promised artifact's owner (the anon target
    /// key) to look up the owner's analysis results via DICE (which will be blocking) to ensure
    /// that any dependent anon target analyses are finished first.
    pub(crate) fn consumer_analysis_artifacts(&self) -> Vec<PromiseArtifact> {
        self.artifacts.map(|e| e.artifact.clone())
    }

    pub(crate) fn register(
        &mut self,
        location: Option<FileSpan>,
        id: PromiseArtifactId,
    ) -> buck2_error::Result<PromiseArtifact> {
        let artifact: PromiseArtifact =
            PromiseArtifact::new(Arc::new(OnceLock::new()), Arc::new(id));

        self.artifacts.push(PromiseArtifactEntry {
            location,
            artifact: artifact.dupe(),
        });
        Ok(artifact)
    }
}

// When passing promise artifacts into anon targets, we will coerce them into this type.
// During resolve, we look up the analysis of the target that produced the promise artifact,
// assert short paths, and produce a new `StarlarkPromiseArtifact` with the `OnceLock` resolved.
#[allow(unused)]
#[derive(Debug, Clone, PartialEq, Eq, Hash, Allocative)]
pub(crate) struct PromiseArtifactAttr {
    pub(crate) id: PromiseArtifactId,
    pub(crate) short_path: Option<ForwardRelativePathBuf>,
}

impl fmt::Display for PromiseArtifactAttr {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        // TODO(@wendyy) - we should figure out what to do about the declaration location.
        // It's possible that 2 targets produce the same promise artifact and try to pass
        // it into a downstream target, so then there would be 2 declaration locations.
        write!(f, "<promise artifact attr (id = {})", self.id)?;
        if let Some(short_path) = &self.short_path {
            write!(f, " with short_path `{}`", short_path)?;
        }
        write!(f, ">")?;
        Ok(())
    }
}
